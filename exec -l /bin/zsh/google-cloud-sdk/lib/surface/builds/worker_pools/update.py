# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Update worker pool command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_exceptions
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import workerpool_config
from googlecloudsdk.api_lib.cloudbuild.v2 import client_util as cloudbuild_v2_util
from googlecloudsdk.api_lib.compute import utils as compute_utils
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.cloudbuild import workerpool_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.UniverseCompatible
class Update(base.UpdateCommand):
  """Update a worker pool used by Cloud Build."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To change the machine type and disk size of workers in a worker pool named wp1, run:

            $ {command} wp1 --region=us-central1 \
                --worker-machine-type=e2-standard-2 \
                --worker-disk-size=64GB
          """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser = workerpool_flags.AddWorkerpoolUpdateArgs(parser,
                                                      base.ReleaseTrack.GA)
    parser.display_info.AddFormat("""
          table(
            name.segment(-1),
            createTime.date('%Y-%m-%dT%H:%M:%S%Oz', undefined='-'),
            state
          )
        """)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """

    return _UpdateWorkerPoolFirstGen(args, self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Update a worker pool used by Cloud Build."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser = workerpool_flags.AddWorkerpoolUpdateArgs(parser,
                                                      base.ReleaseTrack.BETA)
    parser.display_info.AddFormat("""
          table(
            name,
            createTime.date('%Y-%m-%dT%H:%M:%S%Oz', undefined='-'),
            state
          )
        """)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  """Update a private pool used by Cloud Build."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser = workerpool_flags.AddWorkerpoolUpdateArgs(parser,
                                                      base.ReleaseTrack.ALPHA)
    parser.add_argument(
        '--generation',
        default=1,
        type=int,
        help=('Generation of the worker pool.'),
    )
    parser.display_info.AddFormat("""
          table(
            name.segment(-1),
            createTime.date('%Y-%m-%dT%H:%M:%S%Oz', undefined='-'),
            state
          )
        """)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """

    if args.generation == 1:
      return _UpdateWorkerPoolFirstGen(args, self.ReleaseTrack())
    if args.generation == 2:
      return _UpdateWorkerPoolSecondGen(args)

    raise exceptions.InvalidArgumentException(
        '--generation',
        'please use one of the following valid generation values: 1, 2',
    )


def _UpdateWorkerPoolSecondGen(args):
  """Updates a Worker Pool Second Generation.

  Args:
    args: an argparse namespace. All the arguments that were provided to the
        update command invocation.

  Returns:
    A Worker Pool Second Generation resource.
  """
  client = cloudbuild_v2_util.GetClientInstance()
  messages = client.MESSAGES_MODULE

  # Get the workerpool second gen proto from either the flags or the specified
  # file.
  wpsg = messages.WorkerPoolSecondGen()
  if args.config_from_file is not None:
    try:
      wpsg = workerpool_config.LoadWorkerpoolConfigFromPath(
          args.config_from_file, messages.WorkerPoolSecondGen)
    except cloudbuild_exceptions.ParseProtoException as err:
      log.err.Print('\nFailed to parse configuration from file.\n')
      raise err
  else:
    wpsg.worker = messages.WorkerConfig()
    if args.worker_machine_type is not None:
      wpsg.worker.machineType = args.worker_machine_type
    if args.worker_disk_size is not None:
      wpsg.worker.diskStorage = compute_utils.BytesToGb(
          args.worker_disk_size)

  wp_region = args.region
  if not wp_region:
    wp_region = properties.VALUES.builds.region.GetOrFail()

  # Get the workerpool second gen ref
  wp_resource = resources.REGISTRY.Parse(
      None,
      collection='cloudbuild.projects.locations.workerPoolSecondGen',
      api_version=cloudbuild_v2_util.GA_API_VERSION,
      params={
          'projectsId': properties.VALUES.core.project.Get(required=True),
          'locationsId': wp_region,
          'workerPoolSecondGenId': args.WORKER_POOL,
      },
  )

  update_mask = cloudbuild_v2_util.MessageToFieldPaths(wpsg)
  req = messages.CloudbuildProjectsLocationsWorkerPoolSecondGenPatchRequest(
      name=wp_resource.RelativeName(),
      workerPoolSecondGen=wpsg,
      updateMask=','.join(update_mask),
  )
  # Send the Update request
  updated_op = client.projects_locations_workerPoolSecondGen.Patch(req)

  op_resource = resources.REGISTRY.ParseRelativeName(
      updated_op.name, collection='cloudbuild.projects.locations.operations'
  )
  updated_wp = waiter.WaitFor(
      waiter.CloudOperationPoller(
          client.projects_locations_workerPoolSecondGen,
          client.projects_locations_operations,
      ),
      op_resource,
      'Updating worker pool second gen',
  )

  log.UpdatedResource(wp_resource)

  return updated_wp


def _UpdateWorkerPoolFirstGen(args, release_track):
  """Updates a Worker Pool First Generation.

  Args:
    args: an argparse namespace. All the arguments that were provided to the
        update command invocation.
    release_track: The desired value of the enum
      googlecloudsdk.calliope.base.ReleaseTrack.

  Returns:
    A Worker Pool First Generation resource.
  """
  wp_name = args.WORKER_POOL
  wp_region = args.region
  if not wp_region:
    wp_region = properties.VALUES.builds.region.GetOrFail()

  client = cloudbuild_util.GetClientInstance(release_track)
  messages = cloudbuild_util.GetMessagesModule(release_track)

  parent = properties.VALUES.core.project.Get(required=True)

  # Get the workerpool proto from either the flags or the specified file.
  wp = messages.WorkerPool()
  if args.config_from_file is not None:
    try:
      wp = workerpool_config.LoadWorkerpoolConfigFromPath(
          args.config_from_file, messages.WorkerPool)
    except cloudbuild_exceptions.ParseProtoException as err:
      log.err.Print('\nFailed to parse configuration from file.\n')
      raise err
  else:
    wp.privatePoolV1Config = messages.PrivatePoolV1Config()
    worker_config = messages.WorkerConfig()
    if args.worker_machine_type is not None:
      worker_config.machineType = args.worker_machine_type
    if args.worker_disk_size is not None:
      worker_config.diskSizeGb = compute_utils.BytesToGb(
          args.worker_disk_size
      )
    wp.privatePoolV1Config.workerConfig = worker_config

    nc = messages.NetworkConfig()
    # All of the egress flags are mutually exclusive with each other.
    if (args.public_egress is not None and not args.public_egress) or (
        release_track == base.ReleaseTrack.GA and args.no_external_ip
    ):
      nc.egressOption = (
          messages.NetworkConfig.EgressOptionValueValuesEnum.NO_PUBLIC_EGRESS
      )
      wp.privatePoolV1Config.networkConfig = nc
    if args.public_egress:
      nc.egressOption = (
          messages.NetworkConfig.EgressOptionValueValuesEnum.PUBLIC_EGRESS
      )
      wp.privatePoolV1Config.networkConfig = nc

  # Get the workerpool ref
  wp_resource = resources.REGISTRY.Parse(
      None,
      collection='cloudbuild.projects.locations.workerPools',
      api_version=cloudbuild_util.RELEASE_TRACK_TO_API_VERSION[release_track],
      params={
          'projectsId': parent,
          'locationsId': wp_region,
          'workerPoolsId': wp_name,
      })

  update_mask = cloudbuild_util.MessageToFieldPaths(wp)
  req = messages.CloudbuildProjectsLocationsWorkerPoolsPatchRequest(
      name=wp_resource.RelativeName(),
      workerPool=wp,
      updateMask=','.join(update_mask))
  # Send the Update request
  updated_op = client.projects_locations_workerPools.Patch(req)

  op_resource = resources.REGISTRY.ParseRelativeName(
      updated_op.name, collection='cloudbuild.projects.locations.operations')
  updated_wp = waiter.WaitFor(
      waiter.CloudOperationPoller(client.projects_locations_workerPools,
                                  client.projects_locations_operations),
      op_resource, 'Updating worker pool')

  log.UpdatedResource(wp_resource)

  return updated_wp
