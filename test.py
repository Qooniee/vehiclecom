from elm import Elm
import time

emulator = Elm(
    batch_mode=False,           # optional flag to indicate different logging for batch mode
    newline=False,              # optional flag to use newline (<NL>) instead of carriage return <CR> for detecting a line separator
    serial_port="",             # optional serial port used with Windows (ignored with non Windows O.S.)
    serial_baudrate="",         # baud rate used by any serial port (but the forward port); default is 38400 bps
    net_port=None,              # number for the optional TCP/IP network port, alternative to serial_port
    forward_net_host=None,      # host used when forwarding the client interaction to a remote OBD-II device
    forward_net_port=None,      # port used when forwarding the client interaction to a remote OBD-II device
    forward_serial_port=None,   # serial port name when forwarding the client interaction to an OBD-II device via serial communication
    forward_serial_baudrate = None, # used baud rate for the forwarded serial port; default is 38400 bps
    forward_timeout=None)       # floating point number indicating the read timeout when configuring a forwarded OBD-II device; default is 5.0 secs.




with Elm() as session:
    # interactive monitoring
    pty = session.get_pty()
    print(f"Used port: {pty}")
    time.sleep(40) # example