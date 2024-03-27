#-----------------------------------------------------------------------
# runserver.py
# Authors: Jonathan Peixoto & Tinney Mak
#-----------------------------------------------------------------------
import sys
import argparse
import chatbot

#-----------------------------------------------------------------------

# Function to parse command line arguments for the server
def parse_args():
    parser = argparse.ArgumentParser(
        description="The FluentAI application")

    parser.add_argument('port', metavar='port',
     help='the port at which the server should listen')
    return parser.parse_args()

#-----------------------------------------------------------------------
# Main function to set up the server and handle incoming connections
def main():
    # get arguments
    parse_args()

    try:
        port = int(sys.argv[1])
    except Exception:
        print('Port must be an integer.', file = sys.stderr)
        sys.exit(1)

    try:
        chatbot.app.run(host = '0.0.0.0', port = port, debug = True)

    except Exception as ex:
        print(ex, file = sys.stderr)
        sys.exit(1)
#-----------------------------------------------------------------------
if __name__ == "__main__":
    main()
