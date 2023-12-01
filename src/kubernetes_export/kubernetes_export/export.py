import logging
import os
import shutil
import tarfile

from distutils.dir_util import mkpath

import kubernetes_export.context

from lib.k8s_namespaces import Namespaces
from lib.artsy_s3_backup import ArtsyS3Backup
from lib.kctl import Kctl

def backup_to_s3(context, export_dir, local_dir, s3_bucket, s3_prefix):
  ''' back up yamls to S3 '''
  sanitized_context = context.replace('/', '_')
  archive_file = os.path.join(
    local_dir, f"kubernetes-backup-{sanitized_context}.tar.gz"
  )
  logging.info(f"Writing local archive file: {archive_file} ...")

  with tarfile.open(archive_file, "w:gz") as tar:
    tar.add(export_dir, arcname=os.path.basename(export_dir))
  artsy_s3_backup = ArtsyS3Backup(
    s3_bucket,
    s3_prefix,
    'k8s',
    sanitized_context,
    'tar.gz'
  )
  try:
    artsy_s3_backup.backup(archive_file)
  except:
    raise
  finally:
    logging.info(f"Deleting {archive_file} ...")
    os.remove(archive_file)

def export(namespace, object_type, export_dir, kctl):
  ''' export object_type of k8s objects to a yaml file '''
  logging.info(f"Exporting {object_type}...")
  data = kctl.get_namespaced_object(object_type, 'yaml', namespace)
  with open(
    os.path.join(export_dir, namespace, f"{object_type}.yaml"), 'w'
  ) as f:
    f.write('---\n')
    f.write(data)

def export_and_backup(KUBERNETES_OBJECTS, context, in_cluster, local_dir,
                      s3, s3_bucket, s3_prefix, include_namespaces, exclude_namespaces):
  ''' export kubernetes objects to yaml files and optionally back them up to S3 '''
  export_dir = os.path.join(local_dir, context)
  mkpath(export_dir)
  kctl = Kctl(in_cluster, context)
  namespaces_to_export = Namespaces(kctl).namespaces()

  if exclude_namespaces is not None:
    if len(exclude_namespaces) == 1 and exclude_namespaces[0] == 'ALL':
      namespaces_to_export = []
    else:
      for namespace in exclude_namespaces:
        if namespace in namespaces_to_export:
          namespaces_to_export.remove(namespace)

  if include_namespaces is not None:
    for namespace in include_namespaces:
      if namespace not in namespaces_to_export:
        namespaces_to_export.append(namespace)

  namespaces_to_export.sort()

  for namespace in namespaces_to_export:
    namespace_export_dir = os.path.join(export_dir, namespace)
    mkpath(namespace_export_dir)
    logging.info(
      f"Exporting objects from {context} Kubernetes cluster," +
      f" {namespace} namespace, as yaml files, to {namespace_export_dir} ..."
    )
    for object_type in KUBERNETES_OBJECTS:
      export(namespace, object_type, export_dir, kctl)
    logging.info("Done exporting")

  if s3:
    try:
      backup_to_s3(context, export_dir, local_dir, s3_bucket, s3_prefix)
    except:
      raise
    finally:
      logging.info(f"Deleting {export_dir} ...")
      shutil.rmtree(export_dir)
  else:
    logging.info("Skipping backup to S3. Please delete the local files when done!")
