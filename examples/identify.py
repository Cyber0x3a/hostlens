from hostlens import identify

device = identify("192.168.1.42")
print(device.explain())
