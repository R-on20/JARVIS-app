
package com.example.jarvisai

import android.Manifest
import android.content.pm.PackageManager
import android.media.MediaRecorder
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.example.jarvisai.ui.theme.JarvisAITheme
import com.example.jarvisai.ui.theme.jarvis.JarvisScreen
import com.example.jarvisai.ui.theme.jarvis.JarvisState
import okhttp3.Call
import okhttp3.Callback
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import org.json.JSONObject
import java.io.File
import java.io.IOException
import java.util.Locale
import java.util.concurrent.TimeUnit

class MainActivity : ComponentActivity() {

    private var recorder: MediaRecorder? = null

    private var textToSpeech: TextToSpeech? = null
    private var isTtsReady = false

    private lateinit var audioFile: File

    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(120, TimeUnit.SECONDS)
        .readTimeout(180, TimeUnit.SECONDS)
        .callTimeout(240, TimeUnit.SECONDS)
        .build()

    private var isRecording = false

    private var jarvisState by mutableStateOf(
        JarvisState.IDLE
    )

    private var transcript by mutableStateOf("")

    private var responseText by mutableStateOf("")

    private val BASE_URL =
        "https://dream-models-alberta-spoken.trycloudflare.com"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        initializeTextToSpeech()

        requestMicPermission()

        setContent {
            JarvisAITheme(
                dynamicColor = false
            ) {

                JarvisScreen(
                    state = jarvisState,
                    transcript = transcript,
                    response = responseText,

                    onFaceClick = {

                        when (jarvisState) {

                            JarvisState.IDLE -> {
                                startRecording()
                            }

                            JarvisState.LISTENING -> {
                                stopRecording()
                            }

                            JarvisState.ERROR -> {
                                startRecording()
                            }

                            JarvisState.THINKING,
                            JarvisState.SPEAKING -> {
                                // Ignore taps while JARVIS
                                // is processing or speaking.
                            }
                        }
                    }
                )
            }
        }
    }

    // ============================================================
    // INITIALIZE ANDROID TEXT TO SPEECH
    // ============================================================

    private fun initializeTextToSpeech() {

        textToSpeech = TextToSpeech(this) { status ->

            if (status == TextToSpeech.SUCCESS) {

                val languageResult =
                    textToSpeech?.setLanguage(Locale.US)

                if (
                    languageResult == TextToSpeech.LANG_MISSING_DATA ||
                    languageResult == TextToSpeech.LANG_NOT_SUPPORTED
                ) {

                    Log.e(
                        "JARVIS",
                        "English language is not supported by the TTS engine"
                    )

                    isTtsReady = false

                } else {

                    isTtsReady = true

                    Log.d(
                        "JARVIS",
                        "TextToSpeech initialized successfully"
                    )
                }

                textToSpeech?.setOnUtteranceProgressListener(

                    object : UtteranceProgressListener() {

                        override fun onStart(
                            utteranceId: String?
                        ) {

                            runOnUiThread {
                                jarvisState = JarvisState.SPEAKING
                            }

                            Log.d(
                                "JARVIS",
                                "Speaking started"
                            )
                        }

                        override fun onDone(
                            utteranceId: String?
                        ) {

                            runOnUiThread {
                                jarvisState = JarvisState.IDLE
                            }

                            Log.d(
                                "JARVIS",
                                "Speaking finished"
                            )
                        }

                        override fun onError(
                            utteranceId: String?
                        ) {

                            runOnUiThread {
                                jarvisState = JarvisState.ERROR
                            }

                            Log.e(
                                "JARVIS",
                                "TextToSpeech playback failed"
                            )
                        }
                    }
                )

            } else {

                isTtsReady = false

                Log.e(
                    "JARVIS",
                    "TextToSpeech initialization failed"
                )
            }
        }
    }

    // ============================================================
    // MICROPHONE PERMISSION
    // ============================================================

    private fun requestMicPermission() {

        if (
            ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.RECORD_AUDIO
            ) != PackageManager.PERMISSION_GRANTED
        ) {

            ActivityCompat.requestPermissions(
                this,
                arrayOf(
                    Manifest.permission.RECORD_AUDIO
                ),
                1001
            )
        }
    }

    // ============================================================
    // START RECORDING
    // ============================================================

    private fun startRecording() {

        if (
            ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.RECORD_AUDIO
            ) != PackageManager.PERMISSION_GRANTED
        ) {

            requestMicPermission()
            return
        }

        try {

            // Stop any previous speech
            textToSpeech?.stop()

            transcript = ""
            responseText = ""

            audioFile = File(
                cacheDir,
                "voice.m4a"
            )

            recorder = MediaRecorder().apply {

                setAudioSource(
                    MediaRecorder.AudioSource.MIC
                )

                setOutputFormat(
                    MediaRecorder.OutputFormat.MPEG_4
                )

                setAudioEncoder(
                    MediaRecorder.AudioEncoder.AAC
                )

                setOutputFile(
                    audioFile.absolutePath
                )

                prepare()
                start()
            }

            isRecording = true

            jarvisState =
                JarvisState.LISTENING

            Log.d(
                "JARVIS",
                "Listening started"
            )

        } catch (e: Exception) {

            Log.e(
                "JARVIS",
                "Recording failed",
                e
            )

            recorder?.release()
            recorder = null

            isRecording = false

            jarvisState =
                JarvisState.ERROR
        }
    }

    // ============================================================
    // STOP RECORDING
    // ============================================================

    private fun stopRecording() {

        if (!isRecording) {
            return
        }

        try {

            recorder?.stop()

        } catch (e: Exception) {

            Log.e(
                "JARVIS",
                "Recorder stop failed",
                e
            )
        }

        recorder?.release()
        recorder = null

        isRecording = false

        jarvisState =
            JarvisState.THINKING

        Log.d(
            "JARVIS",
            "Listening stopped"
        )

        sendToSTT()
    }

    // ============================================================
    // SPEECH TO TEXT
    // ============================================================

    private fun sendToSTT() {

        val body =
            MultipartBody.Builder()
                .setType(
                    MultipartBody.FORM
                )
                .addFormDataPart(
                    "file",
                    audioFile.name,
                    audioFile.asRequestBody(
                        "audio/*".toMediaTypeOrNull()
                    )
                )
                .build()

        val request =
            Request.Builder()
                .url("$BASE_URL/stt")
                .post(body)
                .build()

        client
            .newCall(request)
            .enqueue(
                object : Callback {

                    override fun onFailure(
                        call: Call,
                        e: IOException
                    ) {

                        Log.e(
                            "JARVIS",
                            "STT failed",
                            e
                        )

                        runOnUiThread {

                            jarvisState =
                                JarvisState.ERROR
                        }
                    }

                    override fun onResponse(
                        call: Call,
                        response: Response
                    ) {

                        val bodyString =
                            response.body?.string()

                        if (!response.isSuccessful) {

                            Log.e(
                                "JARVIS",
                                "STT HTTP error: ${response.code}"
                            )

                            runOnUiThread {

                                jarvisState =
                                    JarvisState.ERROR
                            }

                            return
                        }

                        val userText =
                            try {

                                JSONObject(
                                    bodyString ?: ""
                                ).getString(
                                    "text"
                                )

                            } catch (e: Exception) {

                                Log.e(
                                    "JARVIS",
                                    "STT response parsing failed",
                                    e
                                )

                                null
                            }

                        runOnUiThread {

                            transcript =
                                userText
                                    ?: "Couldn't detect speech"
                        }

                        if (
                            userText != null &&
                            userText.isNotBlank()
                        ) {

                            runOnUiThread {

                                jarvisState =
                                    JarvisState.THINKING
                            }

                            sendToChat(
                                userText
                            )

                        } else {

                            runOnUiThread {

                                jarvisState =
                                    JarvisState.ERROR
                            }
                        }
                    }
                }
            )
    }

    // ============================================================
    // CHAT
    // ============================================================

    private fun sendToChat(
        text: String
    ) {

        val json =
            JSONObject()
                .put(
                    "text",
                    text
                )
                .toString()

        val body =
            json.toRequestBody(
                "application/json"
                    .toMediaTypeOrNull()
            )

        val request =
            Request.Builder()
                .url("$BASE_URL/chat")
                .post(body)
                .build()

        client
            .newCall(request)
            .enqueue(
                object : Callback {

                    override fun onFailure(
                        call: Call,
                        e: IOException
                    ) {

                        Log.e(
                            "JARVIS",
                            "Chat failed",
                            e
                        )

                        runOnUiThread {

                            jarvisState =
                                JarvisState.ERROR
                        }
                    }

                    override fun onResponse(
                        call: Call,
                        response: Response
                    ) {

                        val bodyString =
                            response.body?.string()

                        if (!response.isSuccessful) {

                            Log.e(
                                "JARVIS",
                                "Chat HTTP error: ${response.code}"
                            )

                            runOnUiThread {

                                jarvisState =
                                    JarvisState.ERROR
                            }

                            return
                        }

                        val reply =
                            try {

                                JSONObject(
                                    bodyString ?: ""
                                ).getString(
                                    "reply"
                                )

                            } catch (e: Exception) {

                                Log.e(
                                    "JARVIS",
                                    "Chat response parsing failed",
                                    e
                                )

                                null
                            }

                        if (
                            reply != null &&
                            reply.isNotBlank()
                        ) {

                            runOnUiThread {

                                responseText = reply

                                speakReply(reply)
                            }

                        } else {

                            runOnUiThread {

                                responseText =
                                    "No reply"

                                jarvisState =
                                    JarvisState.ERROR
                            }
                        }
                    }
                }
            )
    }

    // ============================================================
    // SPEAK JARVIS RESPONSE
    // ============================================================

    private fun speakReply(text: String) {

        if (!isTtsReady || textToSpeech == null) {

            Log.e(
                "JARVIS",
                "TextToSpeech is not ready"
            )

            jarvisState = JarvisState.ERROR
            return
        }

        val utteranceId =
            "jarvis-${System.currentTimeMillis()}"

        val result =
            textToSpeech?.speak(
                text,
                TextToSpeech.QUEUE_FLUSH,
                null,
                utteranceId
            )

        if (result == TextToSpeech.ERROR) {

            Log.e(
                "JARVIS",
                "Unable to start speech"
            )

            jarvisState = JarvisState.ERROR
        }
    }

    // ============================================================
    // CLEANUP
    // ============================================================

    override fun onDestroy() {

        recorder?.release()
        recorder = null

        textToSpeech?.stop()
        textToSpeech?.shutdown()
        textToSpeech = null

        super.onDestroy()
    }
}
