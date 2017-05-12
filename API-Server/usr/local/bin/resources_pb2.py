# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: resources.proto

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
  name='resources.proto',
  package='resources',
  syntax='proto3',
  serialized_pb=_b('\n\x0fresources.proto\x12\tresources\"\x1e\n\x02Id\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\n\n\x02id\x18\x02 \x01(\t\"@\n\x10IdsWithinAccount\x12\x11\n\taccountId\x18\x01 \x01(\t\x12\x19\n\x02id\x18\x02 \x03(\x0b\x32\r.resources.IdB>\n1com.cloudera.thunderhead.service.common.resourcesB\tResourcesb\x06proto3')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)




_ID = _descriptor.Descriptor(
  name='Id',
  full_name='resources.Id',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='resources.Id.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='id', full_name='resources.Id.id', index=1,
      number=2, type=9, cpp_type=9, label=1,
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
  serialized_start=30,
  serialized_end=60,
)


_IDSWITHINACCOUNT = _descriptor.Descriptor(
  name='IdsWithinAccount',
  full_name='resources.IdsWithinAccount',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='accountId', full_name='resources.IdsWithinAccount.accountId', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='id', full_name='resources.IdsWithinAccount.id', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
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
  serialized_start=62,
  serialized_end=126,
)

_IDSWITHINACCOUNT.fields_by_name['id'].message_type = _ID
DESCRIPTOR.message_types_by_name['Id'] = _ID
DESCRIPTOR.message_types_by_name['IdsWithinAccount'] = _IDSWITHINACCOUNT

Id = _reflection.GeneratedProtocolMessageType('Id', (_message.Message,), dict(
  DESCRIPTOR = _ID,
  __module__ = 'resources_pb2'
  # @@protoc_insertion_point(class_scope:resources.Id)
  ))
_sym_db.RegisterMessage(Id)

IdsWithinAccount = _reflection.GeneratedProtocolMessageType('IdsWithinAccount', (_message.Message,), dict(
  DESCRIPTOR = _IDSWITHINACCOUNT,
  __module__ = 'resources_pb2'
  # @@protoc_insertion_point(class_scope:resources.IdsWithinAccount)
  ))
_sym_db.RegisterMessage(IdsWithinAccount)


DESCRIPTOR.has_options = True
DESCRIPTOR._options = _descriptor._ParseOptions(descriptor_pb2.FileOptions(), _b('\n1com.cloudera.thunderhead.service.common.resourcesB\tResources'))
import abc
import six
from grpc.beta import implementations as beta_implementations
from grpc.beta import interfaces as beta_interfaces
from grpc.framework.common import cardinality
from grpc.framework.interfaces.face import utilities as face_utilities
# @@protoc_insertion_point(module_scope)
