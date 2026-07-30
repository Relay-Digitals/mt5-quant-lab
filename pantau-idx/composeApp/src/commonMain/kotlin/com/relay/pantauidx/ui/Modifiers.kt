package com.relay.pantauidx.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.composed

/** clickable without the material ripple, matching the design's flat taps. */
fun Modifier.clickableNoRipple(onClick: () -> Unit): Modifier = composed {
    clickable(
        interactionSource = remembered(),
        indication = null,
        onClick = onClick,
    )
}

@Composable
private fun remembered(): MutableInteractionSource {
    return androidx.compose.runtime.remember { MutableInteractionSource() }
}
