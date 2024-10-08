import argparse
import logging
import os

import rabbitmq_export.context

from lib.logging import setup_logging
from lib.util import is_artsy_s3_bucket

class AppConfig:
  def __init__(self, cmdline_args, env):
    ''' set app-wide configs and initialize the app '''
    loglevel, self.artsy_env, self.s3 = (
      cmdline_args.loglevel,
      cmdline_args.artsy_env,
      cmdline_args.s3
    )
    (
      self.local_dir,
      self.rabbitmq_host,
      self.rabbitmq_user,
      self.rabbitmq_pass,
      self.s3_bucket,
      self.s3_prefix
    ) = env
    validate(
      self.rabbitmq_host,
      self.rabbitmq_user,
      self.rabbitmq_pass,
      self.s3,
      self.s3_bucket
    )
    self._init_app(loglevel)

  def _init_app(self, loglevel):
    ''' initialize the app '''
    # initialize logging
    setup_logging(eval('logging.' + loglevel))

def validate(rabbitmq_host, rabbitmq_user, rabbitmq_pass, s3, s3_bucket):
  ''' validate config obtained from env and command line '''
  if not (rabbitmq_host and rabbitmq_user and rabbitmq_pass):
    raise Exception(
      "The following environment variables must be specified: " +
      "RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS"
    )
  if s3 and not s3_bucket:
    raise Exception(
      "RABBITMQ_BACKUP_S3_BUCKET must be specified in the environment."
    )
  if s3 and not is_artsy_s3_bucket(s3_bucket):
    raise Exception(f"{s3_bucket} seems not an Artsy S3 bucket.")

def parse_args():
  ''' parse command line args '''
  parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
  )
  parser.add_argument(
    'artsy_env',
    choices=['staging', 'production'],
    help='the artsy environment of the RabbitMQ instance'
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
    help='indicates to save broker definition to s3'
  )
  return parser.parse_args()

def parse_env(env):
  ''' parse env vars '''
  rabbitmq_host = env.get('RABBITMQ_HOST')
  rabbitmq_user = env.get('RABBITMQ_USER')
  rabbitmq_pass = env.get('RABBITMQ_PASS')
  s3_bucket = env.get('RABBITMQ_BACKUP_S3_BUCKET', '')
  s3_prefix = env.get('RABBITMQ_BACKUP_S3_PREFIX', 'dev')
  # local dir to store exported broker definitions
  local_dir = env.get(
    'LOCAL_DIR', '/tmp/rabbitmq_broker_definitions'
  )
  return (
    local_dir,
    rabbitmq_host,
    rabbitmq_user,
    rabbitmq_pass,
    s3_bucket,
    s3_prefix
  )

# import this from main script
# object will be instantiated only once
config = AppConfig(parse_args(), parse_env(os.environ))
