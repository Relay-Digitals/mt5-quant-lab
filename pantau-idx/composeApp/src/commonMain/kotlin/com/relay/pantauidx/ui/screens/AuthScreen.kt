package com.relay.pantauidx.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.LocalTextStyle
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.relay.pantauidx.AppState
import com.relay.pantauidx.AuthStep
import com.relay.pantauidx.theme.Pantau
import com.relay.pantauidx.ui.clickableNoRipple

@Composable
fun AuthScreen(state: AppState) {
    Column(
        Modifier.fillMaxSize().background(Pantau.Surface).padding(horizontal = 26.dp, vertical = 40.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Text(
            buildAnnotatedString { append("Stock"); withStyle(SpanStyle(color = Pantau.Green)) { append("Pick") } },
            color = Pantau.Text, fontSize = 20.sp, fontWeight = FontWeight.Bold,
        )
        Column(Modifier.padding(top = 22.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(
                if (state.authStep == AuthStep.CREDENTIALS) "Masuk ke akun" else "Verifikasi perangkat",
                color = Pantau.Text, fontSize = 26.sp, fontWeight = FontWeight.Bold,
            )
            Text(
                if (state.authStep == AuthStep.CREDENTIALS)
                    "Login dengan akun Stockbit untuk data IDX live (screener, chart, insider)."
                else state.authInfo ?: "Masukkan kode OTP yang dikirim ke email/HP kamu.",
                color = Pantau.TextDim, fontSize = 13.sp,
            )
        }

        if (state.authStep == AuthStep.CREDENTIALS) CredentialsForm(state) else OtpForm(state)

        state.authError?.let { Text(it, color = Pantau.Red, fontSize = 12.sp) }

        Box(Modifier.height(8.dp))
        Text(
            "Lewati — jelajahi dengan data simulasi",
            color = Pantau.TextDim, fontSize = 13.sp, fontWeight = FontWeight.SemiBold,
            modifier = Modifier.fillMaxWidth().clickableNoRipple { state.continueAsGuest() }.padding(vertical = 6.dp),
        )
    }
}

@Composable
private fun CredentialsForm(state: AppState) {
    var user by remember { mutableStateOf("") }
    var pass by remember { mutableStateOf("") }
    Field("USERNAME / EMAIL", user, { user = it }, KeyboardType.Email)
    Field("PASSWORD", pass, { pass = it }, KeyboardType.Password, password = true)
    Cta(if (state.authBusy) "Memproses…" else "Masuk", enabled = !state.authBusy) { state.login(user, pass) }
}

@Composable
private fun OtpForm(state: AppState) {
    var otp by remember { mutableStateOf("") }
    Field("KODE OTP", otp, { otp = it }, KeyboardType.Number)
    Cta(if (state.authBusy) "Memverifikasi…" else "Verifikasi", enabled = !state.authBusy) { state.verifyOtp(otp) }
}

@Composable
private fun Field(
    label: String,
    value: String,
    onChange: (String) -> Unit,
    keyboard: KeyboardType,
    password: Boolean = false,
) {
    Column(Modifier.fillMaxWidth().padding(top = 6.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
        Text(label, color = Pantau.TextDim, fontSize = 11.sp, fontWeight = FontWeight.SemiBold)
        TextField(
            value = value,
            onValueChange = onChange,
            singleLine = true,
            textStyle = LocalTextStyle.current.copy(color = Pantau.Text, fontSize = 14.sp),
            keyboardOptions = KeyboardOptions(keyboardType = keyboard),
            visualTransformation = if (password) PasswordVisualTransformation() else androidx.compose.ui.text.input.VisualTransformation.None,
            colors = TextFieldDefaults.colors(
                focusedContainerColor = Pantau.Card,
                unfocusedContainerColor = Pantau.Card,
                focusedIndicatorColor = Color.Transparent,
                unfocusedIndicatorColor = Color.Transparent,
                cursorColor = Pantau.Green,
            ),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth().height(52.dp)
                .clip(RoundedCornerShape(12.dp)).border(1.dp, Pantau.Line, RoundedCornerShape(12.dp)),
        )
    }
}

@Composable
private fun Cta(label: String, enabled: Boolean, onClick: () -> Unit) {
    Box(
        Modifier.fillMaxWidth().padding(top = 18.dp).height(52.dp)
            .clip(RoundedCornerShape(13.dp))
            .background(if (enabled) Pantau.Green else Pantau.Line)
            .clickableNoRipple { if (enabled) onClick() },
        contentAlignment = Alignment.Center,
    ) {
        Text(label, color = if (enabled) Pantau.Surface else Pantau.TextDim, fontSize = 15.sp, fontWeight = FontWeight.Bold)
    }
}
