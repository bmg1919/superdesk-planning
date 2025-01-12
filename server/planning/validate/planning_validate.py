# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014, 2015, 2016, 2017, 2018 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

from typing import List

from superdesk import Resource, Service, get_resource_service
from superdesk.metadata.item import ITEM_TYPE
from superdesk.logging import logger

from apps.validate.validate import SchemaValidator as Validator

from copy import deepcopy
from planning.content_profiles.utils import get_enabled_fields

REQUIRED_ERROR = "{} is a required field"


def get_validator_schema(schema):
    """Get schema for given data that will work with validator.

    - if field is required without minlength set make sure it's not empty
    - if there are keys with None value - remove them

    :param schema
    """
    validator_schema = {key: val for key, val in schema.items() if val is not None}

    if validator_schema.get("required") and not validator_schema.get("minlength"):
        validator_schema.setdefault("empty", False)

    return validator_schema


class SchemaValidator(Validator):
    def _validate_validate_on_post(self, validate, field, value):
        """
        {'type': 'boolean'}
        """

        # Ignore this profile as it's to control logic of client side input of Event date range
        pass

    def _validate_field_type(self, field_type, field, value):
        """
        {'type': 'string', 'nullable': True, 'required': False}
        """

        # Ignore this profile as it's for the front-end editor
        pass

    def _validate_expandable(self, expandable, field, value):
        """
        {'type': 'boolean', 'nullable': True}
        """

        # Ignore this profile as it's for the front-end editor
        pass

    def _validate_format_options(self, format_options, field, value):
        """
        {'type': 'list', 'nullable': True}
        """

        # Ignore this profile as it's for the front-end editor
        pass

    def _validate_read_only(self, read_only, field, value):
        """
        {'type': 'boolean', 'nullable': True}
        """

        # Ignore this profile as it's for the front-end editor
        pass

    def _validate_planning_auto_publish(self, planning_auto_publish, field, value):
        """
        {'type': 'boolean', 'nullable': True}
        """
        pass

    def _validate_cancel_plan_with_event(self, cancel_plan_with_event, field, value):
        """
        {'type': 'boolean', 'nullable': True}
        """
        pass

    def _validate_default_language(self, default_language, field, value):
        """
        {'type': string, 'nullable': True}
        """
        pass

    def _validate_languages(self, languages, field, value):
        """
        {'type': 'list', 'nullable': True}
        """
        pass

    def _validate_multilingual(self, multilingual, field, value):
        """
        {'type': 'boolean', 'nullable': True}
        """
        pass

    def _validate_vocabularies(self, vocabularies, field, value):
        """
        {'type': 'list', 'nullable': True}
        """
        pass


class PlanningValidateResource(Resource):
    endpoint_name = "planning_validator"
    schema = {
        "validate_on_post": {"type": "boolean", "default": False},
        "type": {"type": "string", "required": True},
        "validate": {"type": "dict", "required": True},
    }

    resource_methods = ["POST"]
    item_methods: List[str] = []


class PlanningValidateService(Service):
    def create(self, docs, **kwargs):
        for doc in docs:
            test_doc = deepcopy(doc)
            doc["errors"] = self._validate(test_doc)

        return [doc["errors"] for doc in docs]

    def _get_validator(self, doc):
        """Get validators."""
        return get_resource_service("planning_types").find_one(req=None, name=doc[ITEM_TYPE])

    def _get_validator_schema(self, validator, validate_on_post):
        """Get schema for a given validator, excluding fields with None values,
        and only include fields that are in enabled_fields."""

        enabled_fields = get_enabled_fields(validator)
        return {
            field: get_validator_schema(field_schema)
            for field, field_schema in validator["schema"].items()
            if field in enabled_fields
            and field_schema
            and field_schema.get("validate_on_post", False) == validate_on_post
        }

    def _validate(self, doc):
        validator = self._get_validator(doc)

        if validator is None:
            logger.warn("Validator was not found for type:{}".format(doc[ITEM_TYPE]))
            return []

        validation_schema = self._get_validator_schema(validator, doc.get("validate_on_post"))

        v = SchemaValidator()
        v.allow_unknown = True

        try:
            v.validate(doc["validate"], validation_schema)
        except TypeError as e:
            logger.exception('Invalid validator schema value "%s" for ' % str(e))

        error_list = v.errors
        response = []
        for field in error_list:
            error = error_list[field]

            # If error is a list, only return the first error
            if isinstance(error, list):
                error = error[0]

            if error == "empty values not allowed" or error == "required field":
                response.append(REQUIRED_ERROR.format(field.upper()))
            else:
                response.append("{} {}".format(field.upper(), error))

        return response
