package com.example.jarvisai.ui.theme.jarvis

import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import kotlin.math.cos
import kotlin.math.sin

@Composable
fun JarvisFace(
    state: JarvisState,
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(
        label = "jarvis_animation"
    )

    val breathing by infiniteTransition.animateFloat(
        initialValue = 0.96f,
        targetValue = 1.04f,
        animationSpec = infiniteRepeatable(
            animation = tween(
                durationMillis = 1800,
                easing = FastOutSlowInEasing
            ),
            repeatMode = RepeatMode.Reverse
        ),
        label = "breathing"
    )

    val rotation by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(14000),
            repeatMode = RepeatMode.Restart
        ),
        label = "rotation"
    )

    val pulse by infiniteTransition.animateFloat(
        initialValue = 0.65f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(900),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse"
    )

    val speaking by infiniteTransition.animateFloat(
        initialValue = 0.2f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(180),
            repeatMode = RepeatMode.Reverse
        ),
        label = "speaking"
    )

    val stateColor = when (state) {
        JarvisState.IDLE -> Color(0xFF00BFFF)
        JarvisState.LISTENING -> Color(0xFF00E5FF)
        JarvisState.THINKING -> Color(0xFF7C4DFF)
        JarvisState.SPEAKING -> Color(0xFF00FFC6)
        JarvisState.ERROR -> Color(0xFFFF4569)
    }

    Box(modifier = modifier) {

        Canvas(
            modifier = Modifier.fillMaxSize()
        ) {
            val center = Offset(
                size.width / 2f,
                size.height / 2f
            )

            val baseRadius = size.minDimension * 0.28f
            val radius = baseRadius * breathing

            // -----------------------------
            // Outer glow
            // -----------------------------

            drawCircle(
                brush = Brush.radialGradient(
                    colors = listOf(
                        stateColor.copy(alpha = 0.28f),
                        stateColor.copy(alpha = 0.08f),
                        Color.Transparent
                    ),
                    center = center,
                    radius = radius * 1.65f
                ),
                radius = radius * 1.65f,
                center = center
            )

            // -----------------------------
            // Rotating outer ring
            // -----------------------------

            val ringRect = Rect(
                center.x - radius * 1.35f,
                center.y - radius * 1.35f,
                center.x + radius * 1.35f,
                center.y + radius * 1.35f
            )

            drawArc(
                color = stateColor.copy(alpha = 0.35f),
                startAngle = rotation,
                sweepAngle = 100f,
                useCenter = false,
                topLeft = ringRect.topLeft,
                size = ringRect.size,
                style = Stroke(
                    width = 3f,
                    cap = StrokeCap.Round
                )
            )

            drawArc(
                color = stateColor.copy(alpha = 0.18f),
                startAngle = rotation + 180f,
                sweepAngle = 70f,
                useCenter = false,
                topLeft = ringRect.topLeft,
                size = ringRect.size,
                style = Stroke(
                    width = 2f,
                    cap = StrokeCap.Round
                )
            )

            // -----------------------------
            // Face shell
            // -----------------------------

            drawCircle(
                color = Color(0xFF061018).copy(alpha = 0.95f),
                radius = radius,
                center = center
            )

            drawCircle(
                color = stateColor.copy(alpha = 0.5f),
                radius = radius,
                center = center,
                style = Stroke(
                    width = 3f
                )
            )

            // -----------------------------
            // Inner energy ring
            // -----------------------------

            drawCircle(
                color = stateColor.copy(alpha = 0.12f * pulse),
                radius = radius * 0.87f,
                center = center,
                style = Stroke(
                    width = 2f
                )
            )

            // -----------------------------
            // Eyes
            // -----------------------------

            val eyeY = center.y - radius * 0.18f
            val eyeSpacing = radius * 0.38f

            val eyeRadius = when (state) {
                JarvisState.LISTENING -> radius * 0.075f
                JarvisState.SPEAKING -> radius * 0.065f
                else -> radius * 0.06f
            }

            val eyeGlow = stateColor.copy(
                alpha = if (state == JarvisState.IDLE) {
                    0.65f
                } else {
                    1f
                }
            )

            drawCircle(
                color = eyeGlow.copy(alpha = 0.16f),
                radius = eyeRadius * 3.2f,
                center = Offset(
                    center.x - eyeSpacing,
                    eyeY
                )
            )

            drawCircle(
                color = eyeGlow.copy(alpha = 0.16f),
                radius = eyeRadius * 3.2f,
                center = Offset(
                    center.x + eyeSpacing,
                    eyeY
                )
            )

            drawCircle(
                color = eyeGlow,
                radius = eyeRadius,
                center = Offset(
                    center.x - eyeSpacing,
                    eyeY
                )
            )

            drawCircle(
                color = eyeGlow,
                radius = eyeRadius,
                center = Offset(
                    center.x + eyeSpacing,
                    eyeY
                )
            )

            // -----------------------------
            // Eye connection
            // -----------------------------

            drawLine(
                color = stateColor.copy(alpha = 0.22f),
                start = Offset(
                    center.x - eyeSpacing * 0.7f,
                    eyeY
                ),
                end = Offset(
                    center.x + eyeSpacing * 0.7f,
                    eyeY
                ),
                strokeWidth = 1f
            )

            // -----------------------------
            // Mouth
            // -----------------------------

            val mouthY = center.y + radius * 0.27f
            val mouthWidth = radius * 0.42f

            when (state) {

                JarvisState.SPEAKING -> {
                    val mouthHeight =
                        radius * (0.04f + speaking * 0.13f)

                    drawOval(
                        color = stateColor.copy(alpha = 0.9f),
                        topLeft = Offset(
                            center.x - mouthWidth / 2f,
                            mouthY - mouthHeight / 2f
                        ),
                        size = Size(
                            mouthWidth,
                            mouthHeight
                        ),
                        style = Stroke(
                            width = 3f
                        )
                    )
                }

                JarvisState.LISTENING -> {
                    drawArc(
                        color = stateColor,
                        startAngle = 15f,
                        sweepAngle = 150f,
                        useCenter = false,
                        topLeft = Offset(
                            center.x - mouthWidth / 2f,
                            mouthY - radius * 0.03f
                        ),
                        size = Size(
                            mouthWidth,
                            radius * 0.15f
                        ),
                        style = Stroke(
                            width = 3f,
                            cap = StrokeCap.Round
                        )
                    )
                }

                JarvisState.THINKING -> {
                    drawLine(
                        color = stateColor.copy(alpha = 0.9f),
                        start = Offset(
                            center.x - mouthWidth * 0.35f,
                            mouthY
                        ),
                        end = Offset(
                            center.x + mouthWidth * 0.35f,
                            mouthY
                        ),
                        strokeWidth = 3f,
                        cap = StrokeCap.Round
                    )
                }

                JarvisState.ERROR -> {
                    drawArc(
                        color = stateColor,
                        startAngle = 200f,
                        sweepAngle = 140f,
                        useCenter = false,
                        topLeft = Offset(
                            center.x - mouthWidth / 2f,
                            mouthY - radius * 0.08f
                        ),
                        size = Size(
                            mouthWidth,
                            radius * 0.18f
                        ),
                        style = Stroke(
                            width = 3f,
                            cap = StrokeCap.Round
                        )
                    )
                }

                JarvisState.IDLE -> {
                    drawLine(
                        color = stateColor.copy(alpha = 0.75f),
                        start = Offset(
                            center.x - mouthWidth * 0.3f,
                            mouthY
                        ),
                        end = Offset(
                            center.x + mouthWidth * 0.3f,
                            mouthY
                        ),
                        strokeWidth = 2.5f,
                        cap = StrokeCap.Round
                    )
                }
            }

            // -----------------------------
            // Orbit particles
            // -----------------------------

            if (state != JarvisState.IDLE) {

                val particleCount = 12

                for (i in 0 until particleCount) {

                    val angle =
                        rotation * Math.PI / 180.0 +
                                i * (2.0 * Math.PI / particleCount)

                    val particleRadius = radius * 1.48f

                    val x =
                        center.x +
                                cos(angle).toFloat() *
                                particleRadius

                    val y =
                        center.y +
                                sin(angle).toFloat() *
                                particleRadius

                    drawCircle(
                        color = stateColor.copy(
                            alpha = 0.25f + 0.5f * pulse
                        ),
                        radius = if (i % 3 == 0) 4f else 2f,
                        center = Offset(x, y)
                    )
                }
            }
        }
    }
}