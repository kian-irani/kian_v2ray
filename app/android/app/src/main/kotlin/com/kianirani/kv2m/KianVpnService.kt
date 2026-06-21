package com.kianirani.kv2m

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Intent
import android.net.VpnService
import android.os.Build
import android.os.ParcelFileDescriptor

/**
 * The KIAN VPN tunnel service.
 *
 * This establishes the Android tun interface via [VpnService.Builder]. The
 * actual packet processing is handed to the bundled tunnel core (xray-core via
 * its Android .aar) — that native library is added at build time and wired in
 * at [startTunnelCore]. Everything else (lifecycle, tun setup, foreground
 * notification, status) is complete here.
 */
class KianVpnService : VpnService() {

    companion object {
        const val ACTION_START = "com.kianirani.kv2m.START"
        const val ACTION_STOP = "com.kianirani.kv2m.STOP"
        const val EXTRA_CONFIG = "config"
        private const val NOTIF_CHANNEL = "kv2m_vpn"
        private const val NOTIF_ID = 1

        @Volatile
        var currentStatus: String = "disconnected"
            private set
    }

    private var tunInterface: ParcelFileDescriptor? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_STOP -> {
                stopTunnel()
                return START_NOT_STICKY
            }
            else -> {
                val config = intent?.getStringExtra(EXTRA_CONFIG) ?: "{}"
                startTunnel(config)
            }
        }
        return START_STICKY
    }

    private fun startTunnel(config: String) {
        if (tunInterface != null) return
        val builder = Builder()
            .setSession("Kv2m")
            .setMtu(1500)
            .addAddress("10.10.0.2", 32)
            .addDnsServer("1.1.1.1")
            .addDnsServer("8.8.8.8")
            .addRoute("0.0.0.0", 0)        // route all IPv4
            .setBlocking(false)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            builder.setMetered(false)
        }
        tunInterface = builder.establish()
        if (tunInterface == null) {
            currentStatus = "disconnected"
            stopSelf()
            return
        }
        startForeground(NOTIF_ID, buildNotification())
        startTunnelCore(config, tunInterface!!.fd)
        currentStatus = "connected"
    }

    /**
     * Hand the tun fd + config to the native tunnel core. The xray-core .aar
     * exposes a `start(fd, configJson)` entry point; it is added at build time.
     * Until the .aar is bundled this is a no-op so the project still builds.
     */
    private fun startTunnelCore(config: String, tunFd: Int) {
        // TODO(build): bundle xray-core .aar and call its start() here, e.g.
        //   XrayCore.start(tunFd, config)
        // The Dart layer already produces the per-server config JSON.
    }

    private fun stopTunnel() {
        try {
            tunInterface?.close()
        } catch (_: Exception) {
        }
        tunInterface = null
        currentStatus = "disconnected"
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private fun buildNotification(): Notification {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val nm = getSystemService(NotificationManager::class.java)
            nm.createNotificationChannel(
                NotificationChannel(NOTIF_CHANNEL, "Kv2m VPN",
                    NotificationManager.IMPORTANCE_LOW)
            )
        }
        return Notification.Builder(this, NOTIF_CHANNEL)
            .setContentTitle("Kv2m")
            .setContentText("متصل — VPN فعال است")
            .setSmallIcon(android.R.drawable.ic_lock_lock)
            .setOngoing(true)
            .build()
    }

    override fun onDestroy() {
        stopTunnel()
        super.onDestroy()
    }
}
