package com.example.jarvisai

import android.Manifest
import android.content.pm.PackageManager
import android.media.MediaPlayer
import android.media.MediaRecorder
import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.Button
import androidx.appcompat.app.AppCompatActivity
import androidx.compose.animation.core.animate
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File
import java.io.FileOutputStream
import java.io.IOException
import org.json.JSONObject

class MainActivity : AppCompatActivity() {

    private lateinit var recordBtn: Button
    private lateinit var recyclerView: RecyclerView
    private lateinit var adapter: ChatAdapter
    private val messageList = mutableListOf<Message>()

    private var recorder: MediaRecorder? = null
    private lateinit var audioFile: File

    private val client = OkHttpClient()

    private var isRecording = false

    private val BASE_URL = "http://172.31.65.12:8000"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        recordBtn = findViewById(R.id.recordBtn)
        recyclerView = findViewById(R.id.chatRecyclerView)

        adapter = ChatAdapter(messageList)
        recyclerView.adapter = adapter
        recyclerView.layoutManager = LinearLayoutManager(this)

        requestMicPermission()

        recordBtn.setOnClickListener {
            if (!isRecording) {
                startRecording()
            } else {
                stopRecording()
            }
        }
    }

    // ---------- PERMISSIONS ----------
    private fun requestMicPermission() {
        if (ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.RECORD_AUDIO
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.RECORD_AUDIO),
                1001
            )
        }
    }

    // ---------- RECORD ----------
    private fun startRecording() {

        if (ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.RECORD_AUDIO
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            requestMicPermission()
            return
        }

        audioFile = File(cacheDir, "voice.m4a")

        recorder = MediaRecorder().apply {
            setAudioSource(MediaRecorder.AudioSource.MIC)
            setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
            setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
            setOutputFile(audioFile.absolutePath)
            prepare()
            start()
        }

        isRecording = true
        recordBtn.text = "Stop"

        animateOrb()
    }

    private fun stopRecording() {
        try {
            recorder?.stop()
        } catch (e: Exception) {
            e.printStackTrace()
        }

        recorder?.release()
        recorder = null

        isRecording = false
        recordBtn.text = "Record"

        sendToSTT()
        Log.d("JARVIS", "Audio file exists: ${audioFile?.exists()}")
        Log.d("JARVIS", "Audio file size: ${audioFile?.length()}")
    }


    // ---------- STT ----------
    private fun sendToSTT() {
        val body = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart(
                "file",
                audioFile.name,
                audioFile.asRequestBody("audio/*".toMediaTypeOrNull())
            )
            .build()

        val request = Request.Builder()
            .url("$BASE_URL/stt")
            .post(body)
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {}

            override fun onResponse(call: Call, response: Response) {
                val bodyString = response.body?.string()

                val userText = try {
                    val json = JSONObject(bodyString ?: "")
                    json.getString("text")
                } catch (e: Exception) {
                    null
                }

                runOnUiThread {
                    adapter.addMessage(
                        Message(userText ?: "Couldn't detect speech", true)
                    )
                    recyclerView.scrollToPosition(messageList.size - 1)
                }

                if (userText != null) {
                    sendToChat(userText)
                }
            }
        })
    }

    // ---------- CHAT ----------
    private fun sendToChat(text: String) {
        val json = """{"text":"$text"}"""
            .toRequestBody("application/json".toMediaTypeOrNull())

        val request = Request.Builder()
            .url("$BASE_URL/chat")
            .post(json)
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {}

            override fun onResponse(call: Call, response: Response) {
                val body = response.body?.string()
                val reply = try {
                    JSONObject(body ?: "").getString("reply")
                } catch (e: Exception) {
                    null
                }
                runOnUiThread {
                    adapter.addMessage(Message(reply ?: "No reply", false))
                    recyclerView.scrollToPosition(messageList.size - 1)
                }

                if (reply != null) {
                    sendToTTS(reply)
                }
            }
        })
    }

    // ---------- TTS ----------
    private fun sendToTTS(text: String) {
        val json = """{"text":"$text"}"""
            .toRequestBody("application/json".toMediaTypeOrNull())

        val request = Request.Builder()
            .url("$BASE_URL/tts")
            .post(json)
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {}

            override fun onResponse(call: Call, response: Response) {
                val audioBytes = response.body?.bytes() ?: return
                val file = File(cacheDir, "jarvis.mp3")

                val fos = FileOutputStream(file)
                fos.write(audioBytes)
                fos.close()

                playAudio(file)
            }
        })
    }

    // ---------- PLAY ----------
    private fun playAudio(file: File) {
        val player = MediaPlayer()
        player.setDataSource(file.absolutePath)
        player.prepare()
        player.start()
    }
    private fun animateOrb() {
        val orb = findViewById<View>(R.id.aiOrb)

        orb.animate()
            .scaleX(1.2f)
            .scaleY(1.2f)
            .alpha(0.8f)
            .setDuration(800)
            .withEndAction {
                orb.animate()
                    .scaleX(1f)
                    .scaleY(1f)
                    .alpha(1f)
                    .setDuration(800)
                    .start()
            }
            .start()
    }
}