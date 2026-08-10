import asyncio
import socket


async def udp_receiver(shared_rssi: dict[str, int | None], ip: str, port: int, valid_macs: set) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))
    sock.setblocking(False)
    loop = asyncio.get_running_loop()

    print(f"[Receiver] Listening on UDP {port}")
    while True:
        data, addr = await loop.sock_recvfrom(sock, 1024)
        try:
            text = data.decode().strip()
            target_id, mac, rssi_str = text.split(",")
            mac = mac.lower().strip()

            if mac in valid_macs:
                # Direct in-memory write (overwrites previous value for this MAC)
                shared_rssi[mac] = int(rssi_str)
                print(f"[Receiver] {target_id} {mac} rssi={rssi_str}")
            else:
                print(f"[Receiver] Unknown anchor {mac} from {addr[0]}")

        except Exception as exc:
            print(f"[Receiver] Bad packet: {data!r} ({exc})")
