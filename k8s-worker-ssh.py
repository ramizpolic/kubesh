#!/usr/bin/env python3

import sys
import os
import logging
import signal
import warnings
from main.servicetunnel import ServiceTunnel
from main.helpers import MyParser

def keyboardInterruptHandler(signal, frame):
    sys.exit(0)

def main():
    warnings.filterwarnings(
        "ignore", "Your application has authenticated using end user credentials.")

    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s   %(levelname)-8s| %(message)s',
        datefmt='%m-%d-%y %H:%M'
    )

    signal.signal(signal.SIGINT, keyboardInterruptHandler)

    # create parser
    parser = MyParser(description="Tool to create an SSH port-forward to a k8s worker node")
    parser.add_argument("--connect", help="specify node to connect to by name or id", metavar="NODE")
    parser.add_argument("--destroy", action="store_true", help="delete namespace and its contents")
    parser.add_argument("--init", action="store_true", help="create namespace and deploy app")
    parser.add_argument("--list", action="store_true", help="list nodes in k8s cluster")
    args = parser.parse_args()

    # sanity checks
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    if not 'KUBECONFIG' in os.environ:
        logging.error("Need to set KUBECONFIG env variable!")
        sys.exit(1)
    
    # do stuff
    logging.debug("KUBECONFIG is: {}".format(os.environ['KUBECONFIG']))
    st = ServiceTunnel()

    if args.connect:
        st.connect_node(args.connect)

    if args.destroy:
        st.clear_env()

    if args.init:
        st.initialize_env()
        logging.info("Initialized environment successfully.")

    if args.list:
        st.print_nodes()

if __name__ == '__main__':
    main()