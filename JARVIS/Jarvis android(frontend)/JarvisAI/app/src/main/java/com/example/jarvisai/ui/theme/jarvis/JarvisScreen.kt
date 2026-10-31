package com.example.jarvisai.ui.theme.jarvis

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlin.math.abs

@Composable
fun JarvisScreen(
    state: JarvisState,
    onFaceClick: () -> Unit,
    transcript: String = "",
    response: String = ""
) {

    val background = Color(0xFF020609)

    val stateColor = when (state) {
        JarvisState.IDLE -> Color(0xFF00BFFF)
        JarvisState.LISTENING -> Color(0xFF00E5FF)
        JarvisState.THINKING -> Color(0xFF7C4DFF)
        JarvisState.SPEAKING -> Color(0xFF00FFC6)
        JarvisState.ERROR -> Color(0xFFFF4569)
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(background)
    ) {

        // Background stars
        StarField(
            modifier = Modifier.fillMaxSize()
        )

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(
                    horizontal = 24.dp,
                    vertical = 28.dp
                ),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {

            Text(
                text = "J A R V I S",
                color = Color.White,
                fontSize = 22.sp,
                letterSpacing = 7.sp
            )

            Text(
                text = "PERSONAL AI SYSTEM",
                color = stateColor.copy(alpha = 0.7f),
                fontSize = 9.sp,
                letterSpacing = 3.sp
            )

            Spacer(
                modifier = Modifier.height(12.dp)
            )

            StatusIndicator(
                state = state,
                color = stateColor
            )

            Spacer(
                modifier = Modifier.weight(1f)
            )

            Box(
                modifier = Modifier
                    .size(340.dp)
                    .clickable {
                        onFaceClick()
                    },
                contentAlignment = Alignment.Center
            ) {

                JarvisFace(
                    state = state,
                    modifier = Modifier.fillMaxSize()
                )
            }

            Spacer(
                modifier = Modifier.height(20.dp)
            )

            VoiceVisualizer(
                state = state,
                color = stateColor,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(55.dp)
            )

            Spacer(
                modifier = Modifier.height(12.dp)
            )

            val instruction = when (state) {
                JarvisState.IDLE -> "TAP TO SPEAK"
                JarvisState.LISTENING -> "LISTENING..."
                JarvisState.THINKING -> "PROCESSING..."
                JarvisState.SPEAKING -> "JARVIS IS SPEAKING"
                JarvisState.ERROR -> "SYSTEM ERROR"
            }

            Text(
                text = instruction,
                color = stateColor.copy(alpha = 0.85f),
                fontSize = 11.sp,
                letterSpacing = 3.sp
            )

            Spacer(
                modifier = Modifier.height(18.dp)
            )

            AnimatedVisibility(
                visible = transcript.isNotBlank() || response.isNotBlank(),
                enter = fadeIn(),
                exit = fadeOut()
            ) {

                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 8.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {

                    if (transcript.isNotBlank()) {

                        Text(
                            text = "\"$transcript\"",
                            color = Color.White.copy(alpha = 0.65f),
                            fontSize = 13.sp
                        )
                    }

                    if (response.isNotBlank()) {

                        Spacer(
                            modifier = Modifier.height(8.dp)
                        )

                        Text(
                            text = response,
                            color = Color.White.copy(alpha = 0.9f),
                            fontSize = 14.sp
                        )
                    }
                }
            }

            Spacer(
                modifier = Modifier.weight(0.7f)
            )

            Text(
                text = "JARVIS ONLINE",
                color = Color.White.copy(alpha = 0.25f),
                fontSize = 9.sp,
                letterSpacing = 2.sp
            )
        }
    }
}


@Composable
private fun StatusIndicator(
    state: JarvisState,
    color: Color
) {

    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.Center
    ) {

        Box(
            modifier = Modifier
                .size(7.dp)
                .background(
                    color = color,
                    shape = CircleShape
                )
        )

        Spacer(
            modifier = Modifier.size(8.dp)
        )

        Text(
            text = state.name,
            color = color.copy(alpha = 0.8f),
            fontSize = 9.sp,
            letterSpacing = 2.sp
        )
    }
}


@Composable
private fun VoiceVisualizer(
    state: JarvisState,
    color: Color,
    modifier: Modifier = Modifier
) {

    val transition = rememberInfiniteTransition(
        label = "voice_visualizer"
    )

    val movement by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(700),
            repeatMode = RepeatMode.Reverse
        ),
        label = "visualizer"
    )

    Canvas(
        modifier = modifier
    ) {

        val centerY = size.height / 2f

        val bars = 31
        val spacing = size.width / bars

        for (i in 0 until bars) {

            val distance =
                abs(
                    i - bars / 2
                ).toFloat()

            val baseHeight =
                if (state == JarvisState.IDLE) {

                    2f

                } else {

                    7f +
                            (1f - distance / (bars / 2f)) *
                            22f *
                            movement
                }

            drawLine(
                color = color.copy(
                    alpha = if (state == JarvisState.IDLE) {
                        0.2f
                    } else {
                        0.75f
                    }
                ),
                start = Offset(
                    i * spacing,
                    centerY - baseHeight
                ),
                end = Offset(
                    i * spacing,
                    centerY + baseHeight
                ),
                strokeWidth = 2f,
                cap = StrokeCap.Round
            )
        }
    }
}


@Composable
private fun StarField(
    modifier: Modifier = Modifier
) {

    Canvas(
        modifier = modifier
    ) {

        val stars = listOf(
            0.08f to 0.12f,
            0.18f to 0.32f,
            0.31f to 0.16f,
            0.44f to 0.28f,
            0.62f to 0.12f,
            0.77f to 0.22f,
            0.91f to 0.09f,
            0.12f to 0.71f,
            0.27f to 0.83f,
            0.48f to 0.74f,
            0.69f to 0.86f,
            0.86f to 0.68f,
            0.95f to 0.91f
        )

        stars.forEachIndexed { index, position ->

            drawCircle(
                color = Color.White.copy(
                    alpha = if (index % 3 == 0) {
                        0.35f
                    } else {
                        0.15f
                    }
                ),
                radius = if (index % 4 == 0) {
                    2.5f
                } else {
                    1.3f
                },
                center = Offset(
                    size.width * position.first,
                    size.height * position.second
                )
            )
        }
    }
}