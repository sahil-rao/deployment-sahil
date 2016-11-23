# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: version.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='version.proto',
  package='version',
  syntax='proto3',
  serialized_pb=_b('\n\rversion.proto\x12\x07version\"\x10\n\x0eVersionRequest\"\x95\x01\n\x0fVersionResponse\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0f\n\x07version\x18\x02 \x01(\t\x12\x0e\n\x06\x63ommit\x18\x03 \x01(\t\x12\x11\n\ttimestamp\x18\x04 \x01(\t\x12\x13\n\x0b\x62uildNumber\x18\x05 \x01(\t\x12\x0c\n\x04host\x18\x06 \x01(\t\x12\x0c\n\x04user\x18\x07 \x01(\t\x12\x0f\n\x07pokemon\x18\x08 \x01(\tb\x06proto3')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)




_VERSIONREQUEST = _descriptor.Descriptor(
  name='VersionRequest',
  full_name='version.VersionRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=26,
  serialized_end=42,
)


_VERSIONRESPONSE = _descriptor.Descriptor(
  name='VersionResponse',
  full_name='version.VersionResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='version.VersionResponse.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='version', full_name='version.VersionResponse.version', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='commit', full_name='version.VersionResponse.commit', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='timestamp', full_name='version.VersionResponse.timestamp', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='buildNumber', full_name='version.VersionResponse.buildNumber', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='host', full_name='version.VersionResponse.host', index=5,
      number=6, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='user', full_name='version.VersionResponse.user', index=6,
      number=7, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='pokemon', full_name='version.VersionResponse.pokemon', index=7,
      number=8, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=45,
  serialized_end=194,
)

DESCRIPTOR.message_types_by_name['VersionRequest'] = _VERSIONREQUEST
DESCRIPTOR.message_types_by_name['VersionResponse'] = _VERSIONRESPONSE

VersionRequest = _reflection.GeneratedProtocolMessageType('VersionRequest', (_message.Message,), dict(
  DESCRIPTOR = _VERSIONREQUEST,
  __module__ = 'version_pb2'
  # @@protoc_insertion_point(class_scope:version.VersionRequest)
  ))
_sym_db.RegisterMessage(VersionRequest)

VersionResponse = _reflection.GeneratedProtocolMessageType('VersionResponse', (_message.Message,), dict(
  DESCRIPTOR = _VERSIONRESPONSE,
  __module__ = 'version_pb2'
  # @@protoc_insertion_point(class_scope:version.VersionResponse)
  ))
_sym_db.RegisterMessage(VersionResponse)


import abc
import six
from grpc.beta import implementations as beta_implementations
from grpc.beta import interfaces as beta_interfaces
from grpc.framework.common import cardinality
from grpc.framework.interfaces.face import utilities as face_utilities
# @@protoc_insertion_point(module_scope)