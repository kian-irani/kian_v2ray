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

        /**
         * True if a native tunnel core (xray-core / libv2ray .aar) is bundled.
         * Checked by reflection so the project compiles with or without the
         * .aar; once it's added this flips to true automatically.
         */
        fun isCoreAvailable(): Boolean = try {
            Class.forName("libv2ray.Libv2ray")
            true
        } catch (_: Throwable) {
            false
        }
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
        // CRITICAL: never establish a full-tunnel (0.0.0.0/0) unless a real
        // tunnel core is present to forward the packets. Otherwise every packet
        // is routed into the tun and dropped → the device looks "connected" but
        // has NO internet. If there's no core, report it honestly and bail.
        if (!isCoreAvailable()) {
            currentStatus = "no_core"
            stopSelf()
            return
        }
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
        val started = startTunnelCore(config, tunInterface!!.fd)
        if (!started) {
            stopTunnel()              // don't keep a dead tunnel that kills internet
            currentStatus = "no_core"
            return
        }
        startForeground(NOTIF_ID, buildNotification())
        currentStatus = "connected"
    }

    /**
     * Hand the tun fd + config to the native tunnel core. Returns true if the
     * core started. The xray-core .aar exposes a start entry point added at
     * build time. Until the .aar is bundled this returns false (no-op) so the
     * service reports "no_core" instead of black-holing traffic.
     */
    private fun startTunnelCore(config: String, tunFd: Int): Boolean {
        if (!isCoreAvailable()) return false
        // TODO(build): bundle xray-core .aar and call its start() here, e.g.
        //   Libv2ray.newV2RayPoint(...).runLoop(...) with tunFd + config
        return false
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
