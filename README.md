# Kubesh

Tool to access Kubernetes nodes via SSH. 
It creates a port-forward against a pod running socat, allowing SSH via localhost.

Example usage
----

1. pip3 install -r requirements.txt
2. Set *KUBECONFIG* env var to a valid k8s config


```bash
usage: k8s-worker-ssh.py [-h] [--connect NODE] [--destroy] [--init] [--list]

Tool to create an SSH port-forward to a k8s worker node

optional arguments:
  -h, --help      show this help message and exit
  --connect NODE  specify node to connect to by name or id
  --destroy       delete namespace and its contents
  --init          create namespace and deploy app
  --list          list nodes in k8s cluster
```

License
----

MIT
