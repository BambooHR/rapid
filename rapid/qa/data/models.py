"""
 Copyright (c) 2015 Michael Bright and Bamboo HR LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""
import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import UniqueConstraint
from sqlalchemy import Column, String, ForeignKey, Integer, DateTime, Boolean, Text

from rapid.lib import get_declarative_base
from rapid.master.data.database.models.base.active_model import ActiveModel
from rapid.master.data.database.models.base.base_model import BaseModel
# pylint: disable=no-member,too-few-public-methods
Base = get_declarative_base()


class QaTest(BaseModel, Base):
    name = Column(String(1000), nullable=False)
    active = Column(Boolean, default=True)
    qa_test_type_id = Column(Integer, ForeignKey('qa_test_types.id'), nullable=True, index=True)


class QaStatusSummary(BaseModel, Base):
    action_instance_id = Column(Integer, ForeignKey('action_instances.id'), nullable=False, index=True)
    status_id = Column(Integer, ForeignKey('statuses.id'), nullable=False, index=True)
    count = Column(Integer)

    status = relationship('Status')
    action_instance = relationship("ActionInstance", backref="status_summary")


class QaTestHistory(BaseModel, Base):
    test_id = Column(Integer, ForeignKey('qa_tests.id'), nullable=False, index=True)
    pipeline_instance_id = Column(Integer, ForeignKey('pipeline_instances.id'), nullable=False, index=True)
    action_instance_id = Column(Integer, ForeignKey('action_instances.id'), nullable=False, index=True)
    duration = Column(Integer)
    status_id = Column(Integer, ForeignKey('statuses.id'), index=True)
    date_created = Column(DateTime(), nullable=False, default=datetime.datetime.utcnow)

    test = relationship('QaTest')
    pipeline_instance = relationship('PipelineInstance')
    action_instance = relationship('ActionInstance', backref="qa_test_histories")
    status = relationship('Status')
    stacktrace = relationship("Stacktrace", single_parent=True, backref="qa_test_history", cascade="all,delete,delete-orphan")


class Stacktrace(BaseModel, Base):
    qa_test_history_id = Column(Integer, ForeignKey('qa_test_histories.id'), nullable=False, index=True, unique=True)
    stacktrace = Column(Text)


class QaProduct(BaseModel, Base):
    name = Column(String(250), nullable=False, index=True)
    vcs_id = Column(Integer, ForeignKey('vcs.id'), nullable=False, index=True)

    qa_areas = relationship('QaArea', backref="qa_product", order_by="asc(QaArea.name)")
    vcs = relationship('Vcs', backref='qa_product')


class QaArea(BaseModel, Base):
    name = Column(String(250), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("qa_products.id"), nullable=False, index=True)


class QaFeature(BaseModel, Base):
    name = Column(String(250), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("qa_products.id"), nullable=False, index=True)


class QaBehaviorPoint(BaseModel, Base):
    name = Column(String(400), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("qa_products.id"), nullable=False, index=True)


class QaTestMapping(BaseModel, Base):
    area_id = Column(Integer, ForeignKey("qa_areas.id"), nullable=False, index=True)
    feature_id = Column(Integer, ForeignKey('qa_features.id'), index=True)
    behavior_id = Column(Integer, ForeignKey('qa_behavior_points.id'), nullable=False, index=True)
    test_id = Column(Integer, ForeignKey('qa_tests.id'), nullable=False)

    area = relationship('QaArea')
    feature = relationship('QaFeature')
    behavior_point = relationship('QaBehaviorPoint')
    test = relationship('QaTest')

    __table_args__ = (UniqueConstraint('area_id', 'feature_id', 'behavior_id', 'test_id', name="uix_qatm"),)


class QaTestMapTag(BaseModel, Base):
    qa_testmap_id = Column(Integer, ForeignKey('qa_test_mappings.id'), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), nullable=False, index=True)


class Tag(BaseModel, Base):
    name = Column(String(100), nullable=False, index=True)


class QaTestType(ActiveModel, Base):
    pass
