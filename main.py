from message_router import MessageRouter

router = MessageRouter()
router.load_interactions()
router.start_all()

print("🟢 Ready. Send an OSC message to /play on port 9001 to trigger audio.")
print("⏹ Press Enter to quit.\n")

input()
router.stop_all()
print("🛑 Shutdown complete.")
