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

from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import select, union_all
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.schema import Column

from rapid.ci.data.models import Vcs
from rapid.qa.data.models import QaProduct
from rapid.lib.Utils import ORMUtil
from rapid.lib.Constants import Constants, StatusConstants
from rapid.master.data.database import get_db_session
from rapid.master.data.database.dal.GeneralDal import GeneralDal
from rapid.qa.data.models import QaTestHistory, QaStatusSummary, Stacktrace, QaTest, QaArea, QaFeature, QaBehaviorPoint, QaTestMapping
from rapid.workflow.data.models import Status
from rapid.workflow.data.models import PipelineInstance


class QaDal(GeneralDal):
    def reset_results(self, action_instance_id, session):
        """

        :param action_instance_id:
        :type action_instance_id:
        :param session:
        :type session: sqlalchemy.orm.session.Session
        :return:
        :rtype:
        """
        session.execute(Stacktrace.__table__.delete().where(Stacktrace.qa_test_history_id.in_(
            session.query(QaTestHistory.id).filter(QaTestHistory.action_instance_id == action_instance_id))))
        session.execute(QaTestHistory.__table__.delete().where(QaTestHistory.action_instance_id == action_instance_id))
        session.execute(QaStatusSummary.__table__.delete().where(QaStatusSummary.action_instance_id == action_instance_id))

    def save_results(self, action_instance, session, post_data):
        return self._save_results(action_instance, session, post_data)

    def get_test_results(self, action_instance_id, filters=None, session=None):
        results = {}
        if session is None:
            for session in get_db_session():
                query = session.query(QaTestHistory).options(
                    joinedload(QaTestHistory.test)).options(
                    joinedload(QaTestHistory.status)).options(
                    joinedload(QaTestHistory.stacktrace)) \
                    .filter(QaTestHistory.action_instance_id == action_instance_id)
                query = ORMUtil.get_filtered_query(query, filters, QaTestHistory)

                for test_history in query.all():
                    status = test_history.status.name
                    results_array = []
                    if status not in results:
                        results[status] = results_array
                    else:
                        results_array = results[status]
                    results_array.append(test_history.serialize({QaTestHistory.__tablename__: ['test', 'status', 'stacktrace']}))
                return results
        else:
            query = session.query(QaTestHistory).options(
                joinedload(QaTestHistory.test)).options(
                joinedload(QaTestHistory.status)).options(
                joinedload(QaTestHistory.stacktrace)) \
                .filter(QaTestHistory.action_instance_id == action_instance_id)
            query = ORMUtil.get_filtered_query(query, filters, QaTestHistory)

            for test_history in query.all():
                status = test_history.status.name
                results_array = []
                if status not in results:
                    results[status] = results_array
                else:
                    results_array = results[status]
                results_array.append(test_history.serialize(['test', 'status']))
            return results
        return results

    def analyze_tests(self, pipeline_instance_id, json):
        """
        Analyze test results
        :param pipeline_instance_id:
        :type pipeline_instance_id: int
        :param json:
        :type json: dict
        :return:
        :rtype: dict
        """
        if json:
            # Deal with Areas
            # Deal with Features
            # Deal with Behavior Points
            for session in get_db_session():
                product = session.query(QaProduct)\
                    .join(Vcs)\
                    .join(PipelineInstance, PipelineInstance.pipeline_id == Vcs.pipeline_id)\
                    .filter(PipelineInstance.id == pipeline_instance_id).first()

                if product:
                    area_mapper = self._get_area_mapper(session, product.id, json)
                    return area_mapper

        return {}

    def _get_feature_mapper(self, session, joiners, area_mapper, json):
        feature_mapper = {}
        feature_keys = list()

        for area, features in json.iteritems():
            feature_keys.extend(features.keys())

        for feature in session.query(QaFeature).filter(QaFeature.in_(feature_keys)):
            feature_mapper[feature.name] = feature
            del feature_keys[feature.name]

        for feature_name in feature_keys:
            qa_feature = QaFeature(name=feature_name)
            session.add(qa_feature)
            feature_mapper[qa_feature.name] = qa_feature

        session.flush()
        return feature_mapper

    def _get_area_mapper(self, session, product_id, json):
        area_mapper = {}
        feature_mapper = {}
        bp_mapper = {}
        joiner_mapper = {}
        area_keys = []
        feature_keys = []
        bp_keys = []
        test_keys = []
        test_mapper = {}

        for area, area_map in json.items():
            area_keys.append(area)
            area_mapper[area] = {'result': area_mapper, 'model': None}
            for feature, feature_map in area_map.items():
                feature_keys.append(feature)
                feature_mapper[feature] = {'result': feature_map, 'model': None}
                for bp, tests in feature_map.items():
                    bp_keys.append(bp)
                    bp_mapper[bp] = {'result': tests, 'model': None}
                    for test in tests:
                        test_keys.append(test['name'])
                        test['__key__'] = "{}:{}:{}".format(area, feature, bp)
                        test['model'] = None
                        test_mapper[test['name']] = test

        for area in session.query(QaArea).filter(QaArea.name.in_(area_keys)):
            try:
                area_keys.remove(area.name)
            except:
                pass
            area_mapper[area.name]['model'] = area

        for area in area_keys:
            area_model = QaArea(name=area, product_id=product_id)
            session.add(area_model)
            area_mapper[area]['model'] = area_model

        session.flush()

        for feature in session.query(QaFeature).filter(QaFeature.name.in_(feature_keys)):
            try:
                feature_keys.remove(feature.name)
            except:
                pass
            feature_mapper[feature.name]['model'] = feature

        for feature in feature_keys:
            feature_model = QaFeature(name=feature, product_id=product_id)
            session.add(feature_model)
            feature_mapper[feature]['model'] = feature_model

        session.flush()

        for bp in session.query(QaBehaviorPoint).filter(QaBehaviorPoint.name.in_(bp_keys)):
            try:
                bp_keys.remove(bp.name)
            except:
                pass
            bp_mapper[bp.name]['model'] = bp

        for bp in bp_keys:
            bp_model = QaBehaviorPoint(name=bp, product_id=product_id)
            session.add(bp_model)
            bp_mapper[bp]['model'] = bp_model

        session.flush()

        for test, qa_test_mapping in session.query(QaTest, QaTestMapping) \
                .outerjoin(QaTestMapping, QaTest.id == QaTestMapping.test_id) \
                .filter(QaTest.name.in_(test_keys)).all():
            (area, feature, bp) = test_mapper[test.name]['__key__'].split(':')
            if qa_test_mapping is None:
                qa_test_mapping = QaTestMapping(area_id=area_mapper[area]['model'].id,
                                                test_id=test.id,
                                                feature_id=feature_mapper[feature]['model'].id,
                                                behavior_id=bp_mapper[bp]['model'].id)
                session.add(qa_test_mapping)
            else:
                if qa_test_mapping.area_id != area_mapper[area]['model'].id:
                    qa_test_mapping.area_id = area_mapper[area]['model'].id
                if qa_test_mapping.feature_id != feature_mapper[feature]['model'].id:
                    qa_test_mapping.feature_id = feature_mapper[feature]['model'].id
                if qa_test_mapping.behavior_id != bp_mapper[bp]['model'].id:
                    qa_test_mapping.behavior_id = bp_mapper[bp]['model'].id

        session.flush()
        session.commit()

        return {"message": "Success!"}

    def _save_summary(self, action_instance, results, session):
        try:
            if Constants.RESULTS_SUMMARY in results:
                summary = results[Constants.RESULTS_SUMMARY]

                if hasattr(summary, 'keys'):
                    statuses = {}
                    for status in session.query(Status).filter(Status.name.in_(summary.keys())):
                        statuses[status.name] = status

                    for (key, value) in summary.items():
                        if key in statuses:
                            session.add(QaStatusSummary(status_id=statuses[key].id, action_instance_id=action_instance.id, count=value))
                    session.flush()
                del results[Constants.RESULTS_SUMMARY]
        except:
            import traceback
            traceback.print_exc()
        return results

    def _save_results(self, action_instance, session, post_data):
        if 'results' in post_data:
            try:
                results = self._save_summary(action_instance, post_data['results'], session)

                should_create = dict(results)
                test_cache = {}
                for qaTest in session.query(QaTest).filter(QaTest.name.in_(results.keys())):
                    if qaTest.name in should_create:
                        del should_create[qaTest.name]
                        test_cache[qaTest.name] = qaTest

                for name in should_create.keys():
                    qaTest = QaTest(name=name)
                    session.add(qaTest)
                    test_cache[qaTest.name] = qaTest

                session.flush()

                status_cache = {}
                for test, value in results.items():
                    status_id = None
                    if 'status' not in value:
                        status_id = StatusConstants.UNKNOWN

                    if 'status' in value:
                        if value['status'] not in status_cache:
                            status = session.query(Status).filter(func.lower(Status.name) == func.lower(value['status'])).first()
                            if status:
                                status_id = status.id
                                status_cache[status.name] = status
                            else:
                                status_id = StatusConstants.UNKNOWN
                        else:
                            status_id = status_cache[value['status']].id

                    qaTestHistory = QaTestHistory(test_id=test_cache[test].id,
                                                  pipeline_instance_id=action_instance.pipeline_instance_id,
                                                  action_instance_id=action_instance.id,
                                                  status_id=status_id,
                                                  duration=value['time'] if 'time' in value else 0)

                    session.add(qaTestHistory)

                    session.flush()

                    if 'stacktrace' in value:
                        session.add(Stacktrace(qa_test_history_id=qaTestHistory.id, stacktrace=value['stacktrace']))

                session.commit()
            except:
                import traceback
                traceback.print_exc()

    def get_qa_testmap_coverage(self, pipeline_instance_id):
        for session in get_db_session():
            query = session.query(QaTestMapping)\
                           .options(joinedload(QaTestMapping.area))\
                           .options(joinedload(QaTestMapping.feature))\
                           .options(joinedload(QaTestMapping.behavior_point))\
                           .options(joinedload(QaTestMapping.test))\
                           .join(QaTestMapping.area)\
                           .join(QaTestMapping.feature)\
                           .join(QaTestMapping.behavior_point)\
                           .join(QaTestMapping.test)\
                           .join(QaTestHistory, QaTestHistory.test_id == QaTestMapping.test_id)\
                           .filter(QaTestHistory.pipeline_instance_id == pipeline_instance_id)

            mapping = {}
            objects = []
            for (qaTestMapping) in query.all():
                objects.append(qaTestMapping.serialize({QaTestMapping.__tablename__: ['area', 'feature', 'behavior_point', 'test']}))
                # if qaArea.id not in mapping:
                #     mapping[qaArea.id] = qaArea.serialize()
                #     mapping[qaArea.id]['features'] = {}
                #
                # area = mapping[qaArea.id]
                #
                # if qaFeature.id not in area['features']:
                #     area['features'][qaFeature.id] = qaFeature.serialize()
                #     area['features'][qaFeature.id]['behavior_points'] = {}
                #
                # feature = area['features'][qaFeature.id]
                #
                # if qaBehaviorPoint.id not in feature['behavior_points']:
                #     feature['behavior_points'][qaBehaviorPoint.id] = qaBehaviorPoint.serialize()
            return objects
        return {}
