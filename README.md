# Kubesh

Tool to access Kubernetes nodes via SSH. 
It creates a port-forward against a pod running socat, allowing SSH via localhost, and assigns a shell within the cluster.

Example usage
----
```bash
$ pip3 install -r requirements.txt
$ kubesh --help
  usage: k8s-worker-ssh.py [-h] [--connect NODE] [--destroy] [--init] [--list]

  Tool to create an SSH port-forward and shell to a k8s worker node

  optional arguments:
    -h, --help      show this help message and exit
    --connect NODE  specify node to connect to by name or id
    --destroy       delete created resources
    --init          create related resources
    --list          list nodes in k8s cluster

$ kubesh --list
  List of nodes:
    1  gke-eu-cluster-default-pool-00000000-0000
    2  gke-eu-cluster-default-pool-00000001-0001

$ kubesh --init
  Initialized environment successfully.

$ kubesh --connect 1
  Assigning pod 'tunneling-bznrfgxo'
  Pod created, waiting to be ready...
  Pod status is: [Pending]
  Pod status is: [Pending]
  Pod status is: [Running]

  Creating port-forward rules, please wait...
  Forwarding from 127.0.0.1:8022 -> 8022
  Forwarding from [::1]:8022 -> 8022

  Initializing SSH connection...
  Handling connection for 8022

  user@gke-eu-cluster-default-pool-00000000-0000:~ $ echo "hello from k8s cluster"
  user@gke-eu-cluster-default-pool-00000000-0000:~ $ hello from k8s cluster
  user@gke-eu-cluster-default-pool-00000000-0000:~ $ 

$ ./kubesh --destroy
  ================ Roles
  Deleting Role 'tunneling-bznrfgxo'
  ================ Role Bindings
  Deleting Role Binding 'tunneling-bznrfgxo'
  ================ Namespace
  Deleting Namespace 'tunneling'
```

License
----
MIT
