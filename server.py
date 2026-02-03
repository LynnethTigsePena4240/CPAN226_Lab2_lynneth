# This program was modified by lynneth / n01424240
import socket
import argparse
import struct

def run_server(port, output_file):
    # 1. Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # 2. Bind the socket to the port (0.0.0.0 means all interfaces)
    server_address = ('', port)
    print(f"[*] Server listening on port {port}")
    print(f"[*] Server will save each received file as 'received_<ip>_<port>.jpg' based on sender.")
    sock.bind(server_address)
    CHUNK_SIZE = 1400
    # 3. Keep listening for new transfers
    try:
        while True:
            f = None
            sender_filename = None
            reception_started = False

            expected_seq_num = 0
            buffer = {}
            while True:
                data, addr = sock.recvfrom(CHUNK_SIZE + 4) #increased to 4096 + 4 bytes
                # Protocol: If we receive an empty packet, it means "End of File"
                header = data[:4]
                actual_data = data[4:]

                seq_num = struct.unpack('!I', header)[0]

                if not actual_data:
                    if expected_seq_num == seq_num and not buffer:
                        print("=== all packets received. closing file ===")
                        sock.sendto(b'ACK' + struct.pack('!I', seq_num), addr)
                        break

                    else:
                        print( f"[*] EOF received early (seq {seq_num}). "
                              f"expected={expected_seq_num}, buffered={len(buffer)}")
                        sock.sendto(b'ACK' + struct.pack('!I', seq_num), addr)
                        continue
                # start file if not open
                if f is None:
                    print("==== Start of reception ====")
                    ip, sender_port = addr
                    sender_filename = f"received_{ip.replace('.', '_')}_{sender_port}.jpg"
                    f = open(sender_filename, 'wb')
                    print(f"[*] First packet received from {addr}. File opened for writing as '{sender_filename}'.")
                
                # reordering 
                if seq_num == expected_seq_num:
                    # Write data to disk
                    f.seek(seq_num * CHUNK_SIZE)
                    f.write(actual_data)
                    expected_seq_num += 1
                    print(f"[*] wrote packet {seq_num}")

                    while expected_seq_num in buffer:
                        buffered_data = buffer.pop(expected_seq_num)
                        f.seek(expected_seq_num * CHUNK_SIZE)
                        f.write(buffered_data)
                        print(f"[*] wrote buffered packet {expected_seq_num}")
                        expected_seq_num += 1

                elif seq_num > expected_seq_num:
                    if seq_num not in buffer:
                        buffer[seq_num] = actual_data
                        print(f"[!] buffered packet {seq_num} (waiting for {expected_seq_num})")

                else:
                    #duplicated or old packet
                    print(f"[-] ignored duplicate packet {seq_num}")
                # print(f"Server received {len(data)} bytes from {addr}") # Optional: noisy
                sock.sendto(b'ACK' + struct.pack('!I', seq_num), addr)
            if f:
                f.close()
            print("==== End of reception ====")
    except KeyboardInterrupt:
        print("\n[!] Server stopped manually.")
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        sock.close()
        print("[*] Server socket closed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Naive UDP File Receiver")
    parser.add_argument("--port", type=int, default=12001, help="Port to listen on")
    parser.add_argument("--output", type=str, default="received_file.jpg", help="File path to save data")
    args = parser.parse_args()

    try:
        run_server(args.port, args.output)
    except KeyboardInterrupt:
        print("\n[!] Server stopped manually.")
    except Exception as e:
        print(f"[!] Error: {e}")