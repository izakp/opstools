import argparse
import logging
import os

import kubernetes_export.context

from kubernetes_export.export import export_and_backup
from lib.logging import setup_logging

KUBERNETES_OBJECTS = [
    'configmaps',
    'cronjobs',
    'daemonsets',
    'deployments',
    'horizontalpodautoscalers',
    'ingresses',
    'jobs',
    'persistentvolumes',
    'persistentvolumeclaims',
    'poddisruptionbudgets',
    'replicationcontrollers',
    'rolebindings',
    'roles',
    'secrets',
    'serviceaccounts',
    'services',
    'statefulsets'
  ]

def parse_args():
  ''' parse command line args '''
  parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
  )
  parser.add_argument(
    'context',
    help='the context of the target Kubernetes cluster'
  )
  parser.add_argument(
    '--in_cluster',
    action='store_true',
    help='indicates the script is being run inside the target k8s cluster'
  )
  parser.add_argument(
    '--loglevel',
    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
    default='INFO',
    help='log level'
  )
  parser.add_argument(
    '--s3',
    action='store_true',
    help='indicates to save backup to S3'
  )
  parser.add_argument(
    '--include-resources',
    nargs='+',
    help='include additional resource types in backup - takes preference over excluded resources'
  )
  parser.add_argument(
    '--exclude-resources',
    nargs='+',
    help='exclude given resource types from backup, or "ALL" to exclude all'
  )
  parser.add_argument(
    '--include-namespaces',
    nargs='+',
    help='include only the given namespaces in backup - takes preference over excluded namespaces'
  )
  parser.add_argument(
    '--exclude-namespaces',
    nargs='+',
    help='exclude given namespaces from backup, or "ALL" to exclude all'
  )
  return parser.parse_args()

def parse_env():
  ''' parse env vars '''
  s3_bucket = os.environ.get('K8S_BACKUP_S3_BUCKET', '')
  s3_prefix = os.environ.get('K8S_BACKUP_S3_PREFIX', 'dev')
  # local dir to store yamls exported from Kubernetes
  local_dir = os.environ.get('LOCAL_DIR', '/tmp/kubernetes_resources')
  return local_dir, s3_bucket, s3_prefix

if __name__ == "__main__":

  args = parse_args()
  context, in_cluster, loglevel, s3, include_r, exclude_r, include_n, exclude_n = (
    args.context,
    args.in_cluster,
    args.loglevel,
    args.s3,
    args.include_resources,
    args.exclude_resources,
    args.include_namespaces,
    args.exclude_namespaces
  )

  setup_logging(eval('logging.' + loglevel))

  local_dir, s3_bucket, s3_prefix = parse_env()

  kubernetes_objects = KUBERNETES_OBJECTS.copy()

  if exclude_r is not None:
    if len(exclude_r) == 1 and exclude_r[0] == 'ALL':
      kubernetes_objects = []
    else:
      for resource in exclude_r:
        if resource in kubernetes_objects:
          kubernetes_objects.remove(resource)

  if include_r is not None:
    for resource in include_r:
      if resource not in kubernetes_objects:
        kubernetes_objects.append(resource)

  kubernetes_objects.sort()

  export_and_backup(kubernetes_objects, context, in_cluster, local_dir, s3, s3_bucket, s3_prefix, include_n, exclude_n)
