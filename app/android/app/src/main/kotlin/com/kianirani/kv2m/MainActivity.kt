package com.kianirani.kv2m

import android.app.Activity
import android.content.Intent
import android.net.VpnService
import androidx.annotation.NonNull
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

/**
 * Bridges the Flutter UI to the native [KianVpnService] over a MethodChannel.
 *
 * Channel: `kv2m/vpn`
 *   - prepare()        -> requests the system VPN consent dialog if needed
 *   - start(config)    -> starts the tunnel with the given config JSON
 *   - stop()           -> tears the tunnel down
 *   - status()         -> "connected" | "disconnected"
 */
class MainActivity : FlutterActivity() {
    private val channel = "kv2m/vpn"
    private var pendingResult: MethodChannel.Result? = null
    private val vpnRequestCode = 0x7654

    override fun configureFlutterEngine(@NonNull flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, channel)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "prepare" -> prepareVpn(result)
                    "start" -> {
                        val config = call.argument<String>("config") ?: "{}"
                        startVpn(config)
                        result.success(true)
                    }
                    "stop" -> {
                        stopVpn()
                        result.success(true)
                    }
                    "status" -> result.success(KianVpnService.currentStatus)
                    "coreAvailable" -> result.success(KianVpnService.isCoreAvailable())
                    else -> result.notImplemented()
                }
            }
    }

    private fun prepareVpn(result: MethodChannel.Result) {
        val intent = VpnService.prepare(this)
        if (intent != null) {
            pendingResult = result
            startActivityForResult(intent, vpnRequestCode)
        } else {
            result.success(true) // already authorized
        }
    }

    private fun startVpn(config: String) {
        val intent = Intent(this, KianVpnService::class.java).apply {
            action = KianVpnService.ACTION_START
            putExtra(KianVpnService.EXTRA_CONFIG, config)
        }
        startService(intent)
    }

    private fun stopVpn() {
        startService(Intent(this, KianVpnService::class.java).apply {
            action = KianVpnService.ACTION_STOP
        })
    }

    @Deprecated("Deprecated in Java")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == vpnRequestCode) {
            pendingResult?.success(resultCode == Activity.RESULT_OK)
            pendingResult = null
        }
    }
}
