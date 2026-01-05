#!/usr/bin/env python3
"""Cloudflared Ingress Operator.

Watches for Services and Ingresses with cloudflared.io/* annotations
and dynamically updates the cloudflared ConfigMap ingress rules.

Supported annotations:
    cloudflared.io/hostname: "app.example.com"    - Hostname to route (required)
    cloudflared.io/service: "http://service:8080" - (Optional) Override service URL
    cloudflared.io/path: "/*"                     - (Optional) Path-based routing
    cloudflared.io/origin-request: |              - (Optional) Origin request config (YAML)
      connectTimeout: 30s
"""

import logging
import os
import sys
import time
from typing import Any, Dict, List

import yaml
from kubernetes import client, config
from kubernetes.client.rest import ApiException


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


ANNOTATION_HOSTNAME = 'cloudflared.io/hostname'
ANNOTATION_ORIGIN_REQUEST = 'cloudflared.io/origin-request'
ANNOTATION_PATH = 'cloudflared.io/path'
ANNOTATION_PREFIX = 'cloudflared.io/'
ANNOTATION_SERVICE = 'cloudflared.io/service'

CONFIGMAP_NAME = os.getenv('CONFIGMAP_NAME', 'cloudflared')
NAMESPACE = os.getenv('CLOUDFLARED_NAMESPACE', 'default')
WATCH_ALL_NAMESPACES = os.getenv('WATCH_ALL_NAMESPACES', 'true').lower() == 'true'
WATCH_NAMESPACES = os.getenv('WATCH_NAMESPACES', '').split(',') if os.getenv('WATCH_NAMESPACES') else []


class CloudflaredIngressOperator:
    def __init__(self):
        try:
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes config")
        except config.ConfigException:
            try:
                config.load_kube_config()
                logger.info("Loaded kubeconfig from file")
            except config.ConfigException:
                logger.error("Failed to load Kubernetes configuration")
                sys.exit(1)

        self.v1 = client.CoreV1Api()
        self.networking_v1 = client.NetworkingV1Api()


    def get_ingress_rules_from_annotations(self) -> List[Dict[str, Any]]:
        """
        Scan all Services and Ingresses for cloudflared.io/* annotations
        and generate ingress rules.
        """
        ingress_rules = []

        if WATCH_ALL_NAMESPACES:
            services = self.v1.list_service_for_all_namespaces(watch=False)
        else:
            services_list = []
            for ns in WATCH_NAMESPACES or [NAMESPACE]:
                try:
                    ns_services = self.v1.list_namespaced_service(namespace=ns, watch=False)
                    services_list.extend(ns_services.items)
                except ApiException as e:
                    logger.error(f"Error listing services in namespace {ns}: {e}")
            services = type('obj', (object,), {'items': services_list})()

        for svc in services.items:
            if not svc.metadata.annotations:
                continue

            annotations = svc.metadata.annotations

            has_cloudflared_annotations = any(key.startswith(ANNOTATION_PREFIX) for key in annotations.keys())
            if not has_cloudflared_annotations:
                continue

            hostname = annotations.get(ANNOTATION_HOSTNAME)
            if not hostname:
                logger.warning(f"Service {svc.metadata.namespace}/{svc.metadata.name} has "
                             f"cloudflared.io/* annotations but missing {ANNOTATION_HOSTNAME}")
                continue

            service_url = annotations.get(ANNOTATION_SERVICE)
            if not service_url:
                # Auto-generate service URL: http://service-name.namespace:port
                if svc.spec.ports:
                    port = svc.spec.ports[0].port
                    service_url = f"http://{svc.metadata.name}.{svc.metadata.namespace}.svc.cluster.local:{port}"
                else:
                    logger.warning(f"Service {svc.metadata.namespace}/{svc.metadata.name} has no ports")
                    continue

            rule = {'hostname': hostname, 'service': service_url}

            # Optional path-based routing
            path = annotations.get(ANNOTATION_PATH)
            if path:
                rule['path'] = path

            # Optional origin request settings (as YAML/JSON string)
            origin_request = annotations.get(ANNOTATION_ORIGIN_REQUEST)
            if origin_request:
                try:
                    origin_config = yaml.safe_load(origin_request)
                    rule['originRequest'] = origin_config
                except yaml.YAMLError as e:
                    logger.error(f"Invalid YAML in {ANNOTATION_ORIGIN_REQUEST} for "
                               f"{svc.metadata.namespace}/{svc.metadata.name}: {e}")

            ingress_rules.append(rule)
            logger.info(f"Added ingress rule from Service {svc.metadata.namespace}/{svc.metadata.name}: "
                       f"{hostname} -> {service_url}")

        if WATCH_ALL_NAMESPACES:
            ingresses = self.networking_v1.list_ingress_for_all_namespaces(watch=False)
        else:
            ingresses_list = []
            for ns in WATCH_NAMESPACES or [NAMESPACE]:
                try:
                    ns_ingresses = self.networking_v1.list_namespaced_ingress(namespace=ns, watch=False)
                    ingresses_list.extend(ns_ingresses.items)
                except ApiException as e:
                    logger.error(f"Error listing ingresses in namespace {ns}: {e}")
            ingresses = type('obj', (object,), {'items': ingresses_list})()

        for ing in ingresses.items:
            if not ing.metadata.annotations:
                continue

            annotations = ing.metadata.annotations

            has_cloudflared_annotations = any(key.startswith(ANNOTATION_PREFIX) for key in annotations.keys())
            if not has_cloudflared_annotations:
                continue

            # For Ingress resources, we can use the spec to derive rules
            if ing.spec.rules:
                for rule_spec in ing.spec.rules:
                    hostname = annotations.get(ANNOTATION_HOSTNAME, rule_spec.host)
                    if not hostname:
                        continue

                    if rule_spec.http and rule_spec.http.paths:
                        for path_spec in rule_spec.http.paths:
                            backend = path_spec.backend
                            if backend.service:
                                service_name = backend.service.name
                                service_port = backend.service.port.number or backend.service.port.name

                                service_url = annotations.get(ANNOTATION_SERVICE)
                                if not service_url:
                                    service_url = f"http://{service_name}.{ing.metadata.namespace}.svc.cluster.local:{service_port}"

                                rule = {'hostname': hostname, 'service': service_url}

                                if path_spec.path and path_spec.path != '/':
                                    rule['path'] = path_spec.path

                                ingress_rules.append(rule)
                                logger.info(f"Added ingress rule from Ingress {ing.metadata.namespace}/{ing.metadata.name}: "
                                          f"{hostname} -> {service_url}")

        # Sort by hostname for consistent ordering
        ingress_rules.sort(key=lambda x: x.get('hostname', ''))

        return ingress_rules


    def update_configmap(self, ingress_rules: List[Dict[str, Any]]):
        """
        Update the cloudflared ConfigMap with new ingress rules.
        """
        try:
            cm = self.v1.read_namespaced_config_map(name=CONFIGMAP_NAME, namespace=NAMESPACE)
        except ApiException as e:
            logger.error(f"Failed to read ConfigMap {NAMESPACE}/{CONFIGMAP_NAME}: {e}")
            return

        if 'config.yaml' not in cm.data:
            logger.error(f"ConfigMap {NAMESPACE}/{CONFIGMAP_NAME} missing 'config.yaml' key")
            return

        try:
            config_data = yaml.safe_load(cm.data['config.yaml'])
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse config.yaml: {e}")
            return

        # Update ingress rules, keeping the 404 catch-all at the end
        new_ingress = ingress_rules + [{'service': 'http_status:404'}]
        config_data['ingress'] = new_ingress

        # Update ConfigMap
        cm.data['config.yaml'] = yaml.dump(config_data, default_flow_style=False, sort_keys=False)

        try:
            self.v1.patch_namespaced_config_map(name=CONFIGMAP_NAME, namespace=NAMESPACE, body=cm)
            logger.info(f"Successfully updated ConfigMap {NAMESPACE}/{CONFIGMAP_NAME} with {len(ingress_rules)} ingress rules")
        except ApiException as e:
            logger.error(f"Failed to update ConfigMap {NAMESPACE}/{CONFIGMAP_NAME}: {e}")


    def reconcile(self):
        """
        Reconcile: scan all resources and update ConfigMap.
        """
        logger.info("Starting reconciliation...")
        ingress_rules = self.get_ingress_rules_from_annotations()
        self.update_configmap(ingress_rules)
        logger.info("Reconciliation complete")


    def watch_resources(self):
        """
        Watch for changes to Services and Ingresses and trigger reconciliation.
        """
        logger.info("Starting resource watches...")

        while True:
            try:
                # We'll do simple polling instead of complex watch handling
                # In production, you might want to use proper watch with resourceVersion
                self.reconcile()
                time.sleep(30)  # Reconcile every 30 seconds

            except Exception as e:
                logger.error(f"Error in watch loop: {e}", exc_info=True)
                time.sleep(10)


    def run(self):
        """
        Main run loop.
        """
        logger.info(f"Cloudflared Ingress Operator starting...")
        logger.info(f"  ConfigMap: {NAMESPACE}/{CONFIGMAP_NAME}")
        logger.info(f"  Watch all namespaces: {WATCH_ALL_NAMESPACES}")
        if not WATCH_ALL_NAMESPACES:
            logger.info(f"  Watch namespaces: {WATCH_NAMESPACES or [NAMESPACE]}")

        # Initial reconciliation
        self.reconcile()

        # Start watching
        self.watch_resources()


if __name__ == '__main__':
    operator = CloudflaredIngressOperator()
    operator.run()
