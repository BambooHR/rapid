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

from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import UniqueConstraint

from rapid.master.data.database.models.base.ActiveModel import ActiveModel
from rapid.master.data import db
from rapid.master.data.database.models.base.BaseModel import BaseModel


class QaTest(BaseModel, db.Model):
    name = db.Column(db.String(1000), nullable=False)
    active = db.Column(db.Boolean, default=True)
    qa_test_type_id = db.Column(db.Integer, db.ForeignKey('qa_test_types.id'), nullable=True, index=True)


class QaStatusSummary(BaseModel, db.Model):
    action_instance_id = db.Column(db.Integer, db.ForeignKey('action_instances.id'), nullable=False, index=True)
    status_id = db.Column(db.Integer, db.ForeignKey('statuses.id'), nullable=False, index=True)
    count = db.Column(db.Integer)

    status = relationship('Status')
    action_instance = relationship("ActionInstance", backref="status_summary")


class QaTestHistory(BaseModel, db.Model):
    test_id = db.Column(db.Integer, db.ForeignKey('qa_tests.id'), nullable=False, index=True)
    pipeline_instance_id = db.Column(db.Integer, db.ForeignKey('pipeline_instances.id'), nullable=False, index=True)
    action_instance_id = db.Column(db.Integer, db.ForeignKey('action_instances.id'), nullable=False, index=True)
    duration = db.Column(db.Integer)
    status_id = db.Column(db.Integer, db.ForeignKey('statuses.id'), index=True)

    test = relationship('QaTest')
    pipeline_instance = relationship('PipelineInstance')
    action_instance = relationship('ActionInstance', backref="qa_test_histories")
    status = relationship('Status')
    stacktrace = relationship("Stacktrace", single_parent=True, backref="qa_test_history", cascade="all,delete")


class Stacktrace(BaseModel, db.Model):
    qa_test_history_id = db.Column(db.Integer, db.ForeignKey('qa_test_histories.id'), nullable=False, index=True, unique=True)
    stacktrace = db.Column(db.Text)


class QaProduct(BaseModel, db.Model):
    name = db.Column(db.String(250), nullable=False, index=True)
    vcs_id = db.Column(db.Integer, db.ForeignKey('vcs.id'), nullable=False, index=True)

    qa_areas = relationship('QaArea', backref="qa_product", order_by="asc(QaArea.name)")
    vcs = relationship('Vcs', backref='qa_product')


class QaArea(BaseModel, db.Model):
    name = db.Column(db.String(250), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("qa_products.id"), nullable=False, index=True)


class QaFeature(BaseModel, db.Model):
    name = db.Column(db.String(250), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("qa_products.id"), nullable=False, index=True)


class QaBehaviorPoint(BaseModel, db.Model):
    name = db.Column(db.String(400), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("qa_products.id"), nullable=False, index=True)


class QaTestMapping(BaseModel, db.Model):
    area_id = db.Column(db.Integer, db.ForeignKey("qa_areas.id"), nullable=False, index=True)
    feature_id = db.Column(db.Integer, db.ForeignKey('qa_features.id'), index=True)
    behavior_id = db.Column(db.Integer, db.ForeignKey('qa_behavior_points.id'), nullable=False, index=True)
    test_id = db.Column(db.Integer, db.ForeignKey('qa_tests.id'), nullable=False)

    area = relationship('QaArea')
    feature = relationship('QaFeature')
    behavior_point = relationship('QaBehaviorPoint')
    test = relationship('QaTest')

    __table_args__ = (UniqueConstraint('area_id', 'feature_id', 'behavior_id', 'test_id', name="uix_qatm"),)


class QaTestMapTag(BaseModel, db.Model):
    qa_testmap_id = db.Column(db.Integer, db.ForeignKey('qa_test_mappings.id'), nullable=False, index=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=False, index=True)


class Tag(BaseModel, db.Model):
    name = db.Column(db.String(100), nullable=False, index=True)


class QaTestType(ActiveModel, db.Model):
    pass
