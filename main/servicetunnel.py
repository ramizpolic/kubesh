from kubernetes import client, config
from kubernetes.client.rest import ApiException
from .helpers import *
import sys
import os
import logging
import time
import subprocess
import pexpect

class ServiceTunnel():
    """
    Control class for k8s cluster.

    Attributes
    ----------
    namespace : str
        service tunnel namespace (default="tunneling")
    serviceName : str
        service tunnel pod name
    nodes : obj
        k8s node data
    nodeList : dict
        list of k8s nodes with name and address

    Methods
    -------
    initialize_env()
        initializes k8s environment, creates namespace, roles and rolebinding rules.
    print_nodes()
        shows list of nodes from current k8s cluster
    clear_env()
        clears environment
    connect_node(node)
        creates an ssh connection to a k8s cluster node
    """
    namespace = "tunneling"
    serviceName = "tunneling-" + randomstr()

    def __init__(self):
        self.configuration = config.load_kube_config()
        self.api_instance = client.CoreV1Api(client.ApiClient(self.configuration))
        self.rbac_instance = client.RbacAuthorizationV1Api()
    
    """ ----------------- Interface ----------------- """
    def print_nodes(self):
        print("List of nodes: ")
        for i, item in enumerate(self.nodes.items):
            print("%4d  %s" % (i+1, item.metadata.name))
    
    def initialize_env(self):
        self.__createNamespace()

    def clear_env(self):
        print("================ Pods")
        for pod in self.__getPodList().items:
            self.__deletePod(pod.metadata.name, self.namespace)

        print("================ Roles")
        for item in self.__getRoleList().items:
            self.__deleteRole(item.metadata.name)

        print("================ Role Bindings")
        for item in self.__getRoleBindingList().items:
            self.__deleteRoleBinding(item.metadata.name)

        print("================ Namespace")
        self.__deleteNamespace()   
    
    def connect_node(self, node):
        """Creates ssh connection to k8s node.
        
        Arguments:
            node {[str||int]} -- Node name or id
        """
        # check node name validity
        if isInt(node):
            tmplist = list(self.nodeList.keys())
            if len(tmplist) >= int(node) and int(node) > 0:
                node = tmplist[int(node)-1]

        if not self.node_exists(node):
            logging.error("Node doesn't exists, please check node name or id!")
            self.print_nodes()
            sys.exit(1)

        # create pod and roles
        self.__getNamespaceInfo()
        logging.info("Assigning pod '%s'" % self.serviceName)
        self.__createRole()
        self.__createRoleBinding()
        self.__createPod(node)
        logging.info("Pod created, waiting to be ready...")

        # wait until pod is ready
        for i in range(15):
            pod = self.__getPodInfo()
            if pod.status.phase == "Running":
                logging.info("Pod status is: [" + pod.status.phase + "]")
                break
            else:
                logging.info("Pod status is: [" + pod.status.phase + "]")
                time.sleep(2)

        # spawn ssh shell
        self.__createPortForward()
    
    """ ----------------- Attributes ----------------- """
    @property
    def nodes(self):
        return self.__getNodes()

    @property
    def nodeList(self):
        return self.__getNodeList()

    def node_exists(self, node):
        return node in self.nodeList

    """ ----------------- Private ----------------- """
    def __getNodes(self):
        return self.api_instance.list_node()

    def __getPodList(self):
        return self.api_instance.list_namespaced_pod(
            self.namespace, 
            include_uninitialized=False, 
            timeout_seconds=60
        )    
    
    def __getRoleList(self):
        return self.rbac_instance.list_namespaced_role(
            self.namespace, 
            timeout_seconds=60
        )
    
    def __getRoleBindingList(self):
        return self.rbac_instance.list_namespaced_role_binding(
            self.namespace, 
            timeout_seconds=60
        )

    def __getPodInfo(self):
        return self.api_instance.read_namespaced_pod(
            self.serviceName, 
            self.namespace
        )

    def __getNodeList(self):
        __list = {}
        for item in self.nodes.items:
            __list[item.metadata.name] = item.status.addresses[0].address
        return __list

    def __createNamespace(self):
        """Creates namespace in k8s cluster.
        """
        # generate metadata
        body = client.V1Namespace(
            metadata=client.V1ObjectMeta(name=self.namespace)
        )

        # create namespace
        try:
            self.api_instance.create_namespace(body)
        except ApiException as e:
            if e.status == 409:
                pass
            else:
                logging.error(e)
                raise

    def __getNamespaceInfo(self):
        """Gets namespace information.
        """
        # get namespace
        try:
            return self.api_instance.read_namespace(self.namespace)
        except ApiException as e:
            if e.status == 404:
                logging.error("Namespace '%s' does not exist. Please initialize the environment." % self.namespace)
                sys.exit(1)
            else:
                logging.error(e)

    def __deleteNamespace(self):
        """Deletes namespace in k8s cluster.
        """
        # delete namespace
        try:
            self.api_instance.delete_namespace(self.namespace)
            logging.info("Deleting Namespace '%s'" % self.namespace)
        except ApiException as e:
            if e.status == 404:
                pass
            else:
                logging.error(e)

    def __createRole(self):
        """Creates namespace role for ssh tunneling service.
        """
        # TODO: create this dynamically according to user who is using the tool
        # generate metadata
        rules = [
            client.V1PolicyRule(
                api_groups=['policy'],
                resources=['podsecuritypolicies'],
                verbs=['use'],
                resource_names=['gce.privileged']
            )
        ]
        body = client.V1Role(
            metadata=client.V1ObjectMeta(
                name=self.serviceName,
                namespace=self.namespace
            ),
            rules=rules
        )

        # create roles
        try:
            self.rbac_instance.create_namespaced_role(
                namespace=self.namespace,
                body=body
            )
        except ApiException as e:
            if e.status == 409:
                pass
            else:
                logging.error(e)
                raise

    def __createRoleBinding(self):
        """Creates rolebinding for namespaced tunneling service and user.
        """
        # generate metadata
        metadata = client.V1ObjectMeta(
            name=self.serviceName,
            namespace=self.namespace
        )
        subjects = [client.V1Subject(
            name="default",
            kind="ServiceAccount"
        )]
        role_ref = client.V1RoleRef(
            kind="Role",
            api_group="rbac.authorization.k8s.io",
            name=self.namespace
        )
        body = client.V1RoleBinding(
            metadata=metadata,
            subjects=subjects,
            role_ref=role_ref
        )

        # create rolebindings
        try:
            self.rbac_instance.create_namespaced_role_binding(
                namespace=self.namespace,
                body=body
            )
        except ApiException as e:
            if e.status == 409:
                pass
            else:
                logging.error(e)
                raise

    def __deletePod(self, pod, namespace, should_wait = True):
        # delete pod
        try:
            logging.info("Deleting pod '%s'" % pod)
            self.api_instance.delete_namespaced_pod(
                pod, namespace)
        except ApiException as e:
            if e.status == 404:
                pass

        # wait for the pod to be deleted
        if should_wait:
            for i in range(15):
                try:
                    pod = self.__getPodInfo()
                except ApiException as e:
                    if e.status == 404:
                        break
                    else:
                        logging.error(e)
                time.sleep(2)

    def __deleteRole(self, name):
        try:
            logging.info("Deleting Role '%s'" % name)
            self.rbac_instance.delete_namespaced_role(
                name, 
                self.namespace
            )
        except ApiException as e:
            logging.error(e)
    
    def __deleteRoleBinding(self, name):
        try:
            logging.info("Deleting Role Binding '%s'" % name)
            self.rbac_instance.delete_namespaced_role_binding(
                name, 
                self.namespace
            )
        except ApiException as e:
            logging.error(e)

    def __createPod(self, node):
        # TODO: make this a little bit more configurable?
        # generate metadata
        container = client.V1Container(
            name=self.namespace,
            image="toughiq/socat",
            command=["socat"],
            args=["tcp-listen:8022,fork", "tcp:" + node + ":22"]
        )
        spec = client.V1PodSpec(
            containers=[container]
        )
        metadata = client.V1ObjectMeta(
            name=self.serviceName,
            namespace=self.namespace
        )
        body = client.V1Pod(
            metadata=metadata,
            spec=spec
        )

        # create pod
        try:
            self.api_instance.create_namespaced_pod(
                namespace=self.namespace,
                body=body
            )
        except ApiException as e:
            if e.status == 409:
                pass
            else:
                logging.error(e)
                raise

    def __createPortForward(self):
        """Creates ssh connection to tunneling pod."""
        # TODO: use connect_post_namespaced_pod_portforward when it doesn't give a 400 BadRequest
        logging.info("Creating port-forward rules, please wait...")

        # input filter for ssh tty
        def input_filter(s):
            if s == b'\x03':
                return b'\r: Press CTRL-D to exit!\r'
            elif s == b'\x04':
                return b'\nexit\r'
            else:
                return s

        # spawn background process for kubectl port forwarding
        cmd = ['kubectl', 'port-forward',
                    self.serviceName, '8022:8022', '-n', self.namespace]
        p = subprocess.Popen(cmd)

        # create ssh connection
        time.sleep(3)
        logging.info("Initializing SSH connection...")
        try:
            child = pexpect.spawn(
                'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i ~/.ssh/google_compute_engine -p 8022 localhost')
            child.interact(input_filter=input_filter)
            child.sendeof()
            child.expect(pexpect.EOF)
        finally:
            p.terminate()
            self.__deletePod(self.serviceName, self.namespace, False)