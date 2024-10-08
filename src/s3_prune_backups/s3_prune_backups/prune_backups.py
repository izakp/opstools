import logging

import s3_prune_backups.context

from lib.artsy_s3_backup import ArtsyS3Backup
from s3_prune_backups.config import config

def prune():
  ''' delete backups older than ndays '''
  logging.info(
    f"Deleting {config.s3_bucket}/{config.s3_prefix} backups " +
    f"in S3 older than {config.ndays} days..."
  )
  artsy_s3_backup = ArtsyS3Backup(
    config.s3_bucket,
    config.s3_prefix,
    config.suffix
  )
  for backup_id in artsy_s3_backup.old_backups(config.ndays):
    if config.force:
      artsy_s3_backup.delete(backup_id)
      logging.info(f"Deleted {backup_id}")
    else:
      logging.info(f"Would have deleted {backup_id}")
  logging.info(
    f"Done deleting backups"
  )
