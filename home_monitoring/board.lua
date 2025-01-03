--basecode for motherboard

local GPIO = require("periphery").GPIO

local led = GPIO(17, "out")

led:write(true)
os.execute("sleep 1")

led:write(false)

led:close()
