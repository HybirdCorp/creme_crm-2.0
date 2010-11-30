# -*- coding: utf-8 -*-

from datetime import datetime

from django.test import TestCase
from django.contrib.auth.models import User

from creme_core.models import RelationType, CremePropertyType, CremeProperty, CremeEntity
from creme_core.management.commands.creme_populate import Command as PopulateCommand

from persons.models import Contact, Organisation

from commercial.models import *
from commercial.constants import PROP_IS_A_SALESMAN, REL_OBJ_SOLD_BY, REL_SUB_SOLD_BY


class CommercialTestCase(TestCase):
    def login(self):
        if not self.user:
            user = User.objects.create(username='Frodo')
            user.set_password(self.password)
            user.is_superuser = True
            user.save()
            self.user = user

        logged = self.client.login(username=self.user.username, password=self.password)
        self.assert_(logged, 'Not logged in')

    def setUp(self):
        PopulateCommand().handle(application=['creme_core', 'persons', 'commercial'])
        self.password = 'test'
        self.user = None

    def test_commercial01(self): #populate
        try:
            RelationType.objects.get(pk=REL_SUB_SOLD_BY)
            RelationType.objects.get(pk=REL_OBJ_SOLD_BY)
            CremePropertyType.objects.get(pk=PROP_IS_A_SALESMAN)
        except Exception, e:
            self.fail(str(e))

    def test_commapp01(self):
        self.login()

        entity = CremeEntity.objects.create(user=self.user)

        response = self.client.get('/commercial/approach/add/%s/' % entity.id)
        self.assertEqual(response.status_code, 200)

        title       = 'TITLE'
        description = 'DESCRIPTION'
        response = self.client.post('/commercial/approach/add/%s/' % entity.id,
                                    data={
                                            'user':        self.user.pk,
                                            'title':       title,
                                            'description': description,
                                         }
                                   )
        self.assertEqual(response.status_code, 200)

        commapps = CommercialApproach.objects.all()
        self.assertEqual(1, len(commapps))

        commapp = commapps[0]
        self.assertEqual(title,       commapp.title)
        self.assertEqual(description, commapp.description)
        self.assertEqual(entity.id,   commapp.entity_id)

        tdelta = (datetime.today() - commapp.creation_date)
        self.assert_(tdelta.seconds < 10)

    def test_salesman_create(self):
        self.login()

        response = self.client.get('/commercial/salesman/add')
        self.assertEqual(response.status_code, 200)

        first_name = 'John'
        last_name  = 'Doe'

        response = self.client.post('/commercial/salesman/add', follow=True,
                                    data={
                                            'user':       self.user.pk,
                                            'first_name': first_name,
                                            'last_name':  last_name,
                                         }
                                   )
        self.assertEqual(response.status_code, 200)
        self.assert_(response.redirect_chain)
        self.assertEqual(len(response.redirect_chain), 1)

        salesmen = Contact.objects.filter(properties__type=PROP_IS_A_SALESMAN)
        self.assertEqual(1, len(salesmen))

        salesman = salesmen[0]
        self.assertEqual(first_name, salesman.first_name)
        self.assertEqual(last_name,  salesman.last_name)

    def test_salesman_listview01(self):
        self.login()

        self.failIf(Contact.objects.filter(properties__type=PROP_IS_A_SALESMAN).count())

        response = self.client.get('/commercial/salesmen')
        self.assertEqual(response.status_code, 200)

        try:
            salesmen_page = response.context['entities']
        except Exception, e:
            self.fail(str(e))

        self.assertEqual(1, salesmen_page.number)
        self.failIf(salesmen_page.paginator.count)

    def test_salesman_listview02(self):
        self.login()

        self.client.post('/commercial/salesman/add', data={'user': self.user.pk, 'first_name': 'first_name1', 'last_name': 'last_name1'})
        self.client.post('/commercial/salesman/add', data={'user': self.user.pk, 'first_name': 'first_name2', 'last_name': 'last_name2'})
        salesmen = Contact.objects.filter(properties__type=PROP_IS_A_SALESMAN)
        self.assertEqual(2, len(salesmen))

        response = self.client.get('/commercial/salesmen')
        self.assertEqual(response.status_code, 200)

        try:
            salesmen_page = response.context['entities']
        except Exception, e:
            self.fail(str(e))

        self.assertEqual(1, salesmen_page.number)
        self.assertEqual(2, salesmen_page.paginator.count)
        self.assertEqual(set(s.id for s in salesmen), set(o.id for o in salesmen_page.object_list))

    def test_portal(self):
        self.login()
        response = self.client.get('/commercial/')
        self.assertEqual(response.status_code, 200)


class StrategyTestCase(TestCase):
    def setUp(self):
        self.password = 'test'

        user = User.objects.create(username='Bilbo', is_superuser=True)
        user.set_password(self.password)
        user.save()
        self.user = user

        logged = self.client.login(username=user.username, password=self.password)
        self.assert_(logged, 'Not logged in')

    def test_strategy_create(self):
        response = self.client.get('/commercial/strategy/add')
        self.assertEqual(response.status_code, 200)

        name = 'Strat#1'
        response = self.client.post('/commercial/strategy/add', follow=True,
                                    data={
                                            'user': self.user.pk,
                                            'name': name,
                                         }
                                   )
        self.assertEqual(response.status_code, 200)
        self.assert_(response.redirect_chain)
        self.assertEqual(len(response.redirect_chain), 1)

        strategies = Strategy.objects.all()
        self.assertEqual(1, len(strategies))

        strategy = strategies[0]
        self.assertEqual(name, strategy.name)

    def test_strategy_edit(self):
        name = 'Strat#1'
        strategy = Strategy.objects.create(user=self.user, name=name)

        response = self.client.get('/commercial/strategy/edit/%s' % strategy.id)
        self.assertEqual(response.status_code, 200)

        name += '_edited'
        response = self.client.post('/commercial/strategy/edit/%s' % strategy.id, follow=True,
                                    data={
                                            'user': self.user.pk,
                                            'name': name,
                                         })
        self.assertEqual(response.status_code, 200)

        strategy = Strategy.objects.get(pk=strategy.pk)
        self.assertEqual(name, strategy.name)

    def test_segment_add(self):
        strategy = Strategy.objects.create(user=self.user, name='Strat#1')

        response = self.client.get('/commercial/strategy/%s/add/segment/' % strategy.id)
        self.assertEqual(response.status_code, 200)

        name = 'Industry'
        response = self.client.post('/commercial/strategy/%s/add/segment/' % strategy.id,
                                    data={'name': name})
        self.assertEqual(response.status_code, 200)

        segments = strategy.segments.all()
        self.assertEqual(1,    len(segments))
        self.assertEqual(name, segments[0].name)

    def test_segment_edit(self):
        strategy = Strategy.objects.create(user=self.user, name='Strat#1')
        name = 'Industry'
        segment = MarketSegment.objects.create(name=name, strategy=strategy)

        response = self.client.get('/commercial/segment/edit/%s/' % segment.id)
        self.assertEqual(response.status_code, 200)

        name += 'of Cheese'
        response = self.client.post('/commercial/segment/edit/%s/' % segment.id,
                                    data={'name': name})
        self.assertEqual(response.status_code, 200)

        segment = MarketSegment.objects.get(pk=segment.pk)
        self.assertEqual(name,        segment.name)
        self.assertEqual(strategy.id, segment.strategy_id)

    def test_segment_delete(self):
        strategy = Strategy.objects.create(user=self.user, name='Strat#1')
        segment = MarketSegment.objects.create(name='Industry', strategy=strategy)
        self.assertEqual(1, len(strategy.segments.all()))

        response = self.client.post('/commercial/segment/delete', data={'id': segment.id}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(0, len(strategy.segments.all()))

    def test_asset_add(self):
        strategy = Strategy.objects.create(user=self.user, name='Strat#1')

        response = self.client.get('/commercial/strategy/%s/add/asset/' % strategy.id)
        self.assertEqual(response.status_code, 200)

        name = 'Size'
        response = self.client.post('/commercial/strategy/%s/add/asset/' % strategy.id,
                                    data={'name': name})
        self.assertEqual(response.status_code, 200)

        assets = strategy.assets.all()
        self.assertEqual(1, len(assets))
        self.assertEqual(name, assets[0].name)

    def test_asset_edit(self):
        strategy = Strategy.objects.create(user=self.user, name='Strat#1')
        name = 'Size'
        asset = CommercialAsset.objects.create(name=name, strategy=strategy)

        response = self.client.get('/commercial/asset/edit/%s/' % asset.id)
        self.assertEqual(response.status_code, 200)

        name += '_edited'
        response = self.client.post('/commercial/asset/edit/%s/' % asset.id,
                                    data={'name': name})
        self.assertEqual(response.status_code, 200)

        asset = CommercialAsset.objects.get(pk=asset.pk)
        self.assertEqual(name,        asset.name)
        self.assertEqual(strategy.id, asset.strategy_id)

    def test_asset_delete(self):
        strategy = Strategy.objects.create(user=self.user, name='Strat#1')
        asset = CommercialAsset.objects.create(name='Capital', strategy=strategy)
        self.assertEqual(1, len(strategy.assets.all()))

        response = self.client.post('/commercial/asset/delete', data={'id': asset.id}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(0, len(strategy.assets.all()))

    def test_charms_add(self):
        strategy = Strategy.objects.create(user=self.user, name='Strat#1')

        response = self.client.get('/commercial/strategy/%s/add/charm/' % strategy.id)
        self.assertEqual(response.status_code, 200)

        name = 'Size'
        response = self.client.post('/commercial/strategy/%s/add/charm/' % strategy.id,
                                    data={'name': name})
        self.assertEqual(response.status_code, 200)

        charms = strategy.charms.all()
        self.assertEqual(1,    len(charms))
        self.assertEqual(name, charms[0].name)

    def test_charm_edit(self):
        strategy = Strategy.objects.create(user=self.user, name='Strat#1')
        name = 'Size'
        charm = MarketSegmentCharm.objects.create(name=name, strategy=strategy)

        response = self.client.get('/commercial/charm/edit/%s/' % charm.id)
        self.assertEqual(response.status_code, 200)

        name += '_edited'
        response = self.client.post('/commercial/charm/edit/%s/' % charm.id,
                                    data={'name': name})
        self.assertEqual(response.status_code, 200)

        charm = MarketSegmentCharm.objects.get(pk=charm.pk)
        self.assertEqual(name,        charm.name)
        self.assertEqual(strategy.id, charm.strategy_id)

    def test_charm_delete(self):
        strategy = Strategy.objects.create(user=self.user, name='Strat#1')
        charm = MarketSegmentCharm.objects.create(name='Dollars', strategy=strategy)
        self.assertEqual(1, len(strategy.charms.all()))

        response = self.client.post('/commercial/charm/delete', data={'id': charm.id}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(0, len(strategy.charms.all()))

    def test_evaluated_orga(self):
        strategy = Strategy.objects.create(user=self.user, name='Strat#1')
        orga     = Organisation.objects.create(user=self.user, name='Nerv')

        response = self.client.get('/commercial/strategy/%s/add/organisation/' % strategy.id)
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/commercial/strategy/%s/add/organisation/' % strategy.id,
                                    data={'organisations': orga.id})
        self.assertEqual(response.status_code, 200)

        orgas = strategy.evaluated_orgas.all()
        self.assertEqual(1,       len(orgas))
        self.assertEqual(orga.pk, orgas[0].pk)

        response = self.client.get('/commercial/strategy/%s/organisation/%s' % (strategy.id, orga.id))
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/commercial/strategy/%s/organisation/delete' % strategy.id,
                                    data={'id': orga.id}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(0, len(strategy.evaluated_orgas.all()))

    def _set_asset_score(self, strategy, orga, asset, segment, score):
        response = self.client.post('/commercial/strategy/%s/set_asset_score' % strategy.id,
                                    data={
                                            'asset_id':   asset.id,
                                            'segment_id': segment.id,
                                            'orga_id':    orga.id,
                                            'score':      score,
                                         }
                                   )
        self.assertEqual(200, response.status_code)

    def test_set_asset_score01(self):
        strategy = Strategy.objects.create(user=self.user, name='Strat#1')
        segment  = MarketSegment.objects.create(name='Industry', strategy=strategy)
        asset    = CommercialAsset.objects.create(name='Capital', strategy=strategy)

        orga = Organisation.objects.create(user=self.user, name='Nerv')
        strategy.evaluated_orgas.add(orga)

        self.assertEqual(1, strategy.get_asset_score(orga, asset, segment))
        self.assertEqual([(1, 3)], strategy.get_segments_totals(orga))

        score = 3
        self._set_asset_score(strategy, orga, asset, segment, score)

        strategy = Strategy.objects.get(pk=strategy.pk) #refresh object (cache....)
        self.assertEqual(score, strategy.get_asset_score(orga, asset, segment))
        self.assertEqual([(score, 3)], strategy.get_segments_totals(orga))

    def test_set_asset_score02(self):
        strategy = Strategy.objects.create(user=self.user, name='Strat#1')

        create_segment = MarketSegment.objects.create
        segment01 = create_segment(name='Industry', strategy=strategy)
        segment02 = create_segment(name='People', strategy=strategy)

        create_asset = CommercialAsset.objects.create
        asset01 = create_asset(name='Capital', strategy=strategy)
        asset02 = create_asset(name='Size', strategy=strategy)

        orga = Organisation.objects.create(user=self.user, name='Nerv')
        strategy.evaluated_orgas.add(orga)

        self.assertEqual(1, strategy.get_asset_score(orga, asset01, segment01))
        self.assertEqual(1, strategy.get_asset_score(orga, asset01, segment02))
        self.assertEqual(1, strategy.get_asset_score(orga, asset02, segment01))
        self.assertEqual(1, strategy.get_asset_score(orga, asset02, segment02))

        self.assertEqual([(2, 3), (2, 3)], strategy.get_segments_totals(orga))

        score11 = 1; score12 = 4; score21 = 3; score22 = 2
        self._set_asset_score(strategy, orga, asset01, segment01, score11)
        self._set_asset_score(strategy, orga, asset01, segment02, score12)
        self._set_asset_score(strategy, orga, asset02, segment01, score21)
        self._set_asset_score(strategy, orga, asset02, segment02, score22)

        strategy = Strategy.objects.get(pk=strategy.pk) #refresh object (cache....)
        self.assertEqual(score11, strategy.get_asset_score(orga, asset01, segment01))
        self.assertEqual(score12, strategy.get_asset_score(orga, asset01, segment02))
        self.assertEqual(score21, strategy.get_asset_score(orga, asset02, segment01))
        self.assertEqual(score22, strategy.get_asset_score(orga, asset02, segment02))

        self.assertEqual([(score11 + score21, 1), (score12 + score22, 3)], strategy.get_segments_totals(orga))

    def test_delete01(self):
        strategy = Strategy.objects.create(user=self.user, name='Strat#1')
        self.assertEqual(1, Strategy.objects.count())

        strategy.delete()
        self.assertEqual(0, Strategy.objects.count())

    #TODO: complete (MarketSegmentCharmScore ??)
    def test_delete02(self):
        strategy = Strategy.objects.create(user=self.user, name='Strat#1')
        segment  = MarketSegment.objects.create(name='Industry', strategy=strategy)
        asset    = CommercialAsset.objects.create(name='Capital', strategy=strategy)
        charm    = MarketSegmentCharm.objects.create(name='Celebrity', strategy=strategy)

        orga = Organisation.objects.create(user=self.user, name='Nerv')
        strategy.evaluated_orgas.add(orga)

        self._set_asset_score(strategy, orga, asset, segment, 2)

        self.assertEqual(1, Strategy.objects.count())
        self.assertEqual(1, MarketSegment.objects.count())
        self.assertEqual(1, CommercialAsset.objects.count())
        self.assertEqual(1, MarketSegmentCharm.objects.count())
        self.assertEqual(1, CommercialAssetScore.objects.count())

        strategy.delete()
        self.assertEqual(0, Strategy.objects.count())
        self.assertEqual(0, MarketSegment.objects.count())
        self.assertEqual(0, CommercialAsset.objects.count())
        self.assertEqual(0, MarketSegmentCharm.objects.count())
        self.assertEqual(0, CommercialAssetScore.objects.count())

#TODO: tests for Act, (SellByRelation)
