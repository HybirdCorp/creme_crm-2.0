# -*- coding: utf-8 -*-

from django.conf.urls import url

from creme.creme_core.conf.urls import Swappable, swap_manager

from creme.persons import contact_model_is_custom

from creme.opportunities import opportunity_model_is_custom

from . import act_model_is_custom, pattern_model_is_custom, strategy_model_is_custom
from .views import commercial_approach, market_segment, act, salesman, strategy  # portal


urlpatterns = [
    # url(r'^$', portal.portal, name='commercial__portal'),

    # url(r'^approach/add/(?P<entity_id>\d+)[/]?$', commercial_approach.add, name='commercial__create_approach'),
    url(r'^approach/add/(?P<entity_id>\d+)[/]?$',
        commercial_approach.CommercialApproachCreation.as_view(),
        name='commercial__create_approach',
       ),

    # Segments
    # url(r'^market_segments[/]?$',                           market_segment.listview, name='commercial__list_segments'),
    url(r'^market_segments[/]?$',                           market_segment.Segments.as_view(),        name='commercial__list_segments'),
    # url(r'^market_segment/add[/]?$',                        market_segment.add,      name='commercial__create_segment'),
    url(r'^market_segment/add[/]?$',                        market_segment.SegmentCreation.as_view(), name='commercial__create_segment'),
    # url(r'^market_segment/edit/(?P<segment_id>\d+)[/]?$',   market_segment.edit,     name='commercial__edit_segment'),
    url(r'^market_segment/edit/(?P<segment_id>\d+)[/]?$',   market_segment.SegmentEdition.as_view(),  name='commercial__edit_segment'),
    # url(r'^market_segment/delete/(?P<segment_id>\d+)[/]?$', market_segment.delete,   name='commercial__delete_segment'),
    url(r'^market_segment/delete/(?P<segment_id>\d+)[/]?$', market_segment.SegmentDeletion.as_view(), name='commercial__delete_segment'),

    # Objectives & opportunities
    # url(r'^act/(?P<act_id>\d+)/add/objective[/]?$',               act.add_objective,               name='commercial__create_objective'),
    url(r'^act/(?P<act_id>\d+)/add/objective[/]?$',               act.ObjectiveCreation.as_view(),             name='commercial__create_objective'),
    # url(r'^act/(?P<act_id>\d+)/add/objectives_from_pattern[/]?$', act.add_objectives_from_pattern, name='commercial__create_objective_from_pattern'),
    url(r'^act/(?P<act_id>\d+)/add/objectives_from_pattern[/]?$', act.ObjectivesCreationFromPattern.as_view(), name='commercial__create_objective_from_pattern'),  # TODO: commercial__create_objectiveS_from_pattern
    # url(r'^objective/(?P<objective_id>\d+)/edit[/]?$',            act.edit_objective,              name='commercial__edit_objective'),
    url(r'^objective/(?P<objective_id>\d+)/edit[/]?$',            act.ObjectiveEdition.as_view(),              name='commercial__edit_objective'),
    url(r'^objective/(?P<objective_id>\d+)/incr[/]?$',            act.incr_objective_counter,                  name='commercial__incr_objective_counter'),
    # url(r'^objective/(?P<objective_id>\d+)/create_entity[/]?$',   act.create_objective_entity,     name='commercial__create_entity_from_objective'),
    url(r'^objective/(?P<objective_id>\d+)/create_entity[/]?$',   act.RelatedEntityCreation.as_view(),         name='commercial__create_entity_from_objective'),

    # Pattern component
    # url(r'^objective_pattern/(?P<objpattern_id>\d+)/add_component[/]?$',      act.add_pattern_component,        name='commercial__create_component'),
    url(r'^objective_pattern/(?P<objpattern_id>\d+)/add_component[/]?$',      act.PatternComponentCreation.as_view(),       name='commercial__create_component'),
    # url(r'^objective_pattern/component/(?P<component_id>\d+)/add_child[/]$',  act.add_child_pattern_component,  name='commercial__create_child_component'),
    url(r'^objective_pattern/component/(?P<component_id>\d+)/add_child[/]$',  act.ChildPatternComponentCreation.as_view(),  name='commercial__create_child_component'),
    # url(r'^objective_pattern/component/(?P<component_id>\d+)/add_parent[/]$', act.add_parent_pattern_component, name='commercial__create_parent_component'),
    url(r'^objective_pattern/component/(?P<component_id>\d+)/add_parent[/]$', act.ParentPatternComponentCreation.as_view(), name='commercial__create_parent_component'),

    # Segments
    # url(r'^strategy/(?P<strategy_id>\d+)/add/segment[/]?$',                      strategy.add_segment,  name='commercial__create_segment_desc'),
    url(r'^strategy/(?P<strategy_id>\d+)/add/segment[/]?$',  strategy.SegmentDescCreation.as_view(), name='commercial__create_segment_desc'),
    # url(r'^strategy/(?P<strategy_id>\d+)/link/segment[/]?$',                     strategy.link_segment, name='commercial__link_segment'),
    url(r'^strategy/(?P<strategy_id>\d+)/link/segment[/]?$', strategy.SegmentLinking.as_view(),      name='commercial__link_segment'),
    # url(r'^strategy/(?P<strategy_id>\d+)/segment/edit/(?P<seginfo_id>\d+)[/]?$', strategy.edit_segment, name='commercial__edit_segment_desc'),
    url(r'^segment_desc/edit/(?P<segdesc_id>\d+)[/]?$',      strategy.SegmentDescEdition.as_view(),  name='commercial__edit_segment_desc'),

    # Assets
    # url(r'^strategy/(?P<strategy_id>\d+)/add/asset[/]?$', strategy.add_asset,  name='commercial__create_asset'),
    url(r'^strategy/(?P<strategy_id>\d+)/add/asset[/]?$', strategy.AssetCreation.as_view(), name='commercial__create_asset'),
    # url(r'^asset/edit/(?P<asset_id>\d+)[/]?$',            strategy.edit_asset, name='commercial__edit_asset'),
    url(r'^asset/edit/(?P<asset_id>\d+)[/]?$',            strategy.AssetEdition.as_view(),  name='commercial__edit_asset'),

    # Charms
    # url(r'^strategy/(?P<strategy_id>\d+)/add/charm[/]?$', strategy.add_charm,  name='commercial__create_charm'),
    url(r'^strategy/(?P<strategy_id>\d+)/add/charm[/]?$', strategy.CharmCreation.as_view(), name='commercial__create_charm'),
    # url(r'^charm/edit/(?P<charm_id>\d+)[/]?$',            strategy.edit_charm, name='commercial__edit_charm'),
    url(r'^charm/edit/(?P<charm_id>\d+)[/]?$',            strategy.CharmEdition.as_view(),  name='commercial__edit_charm'),

    # Evaluated organisations
    # url(r'^strategy/(?P<strategy_id>\d+)/add/organisation[/]?$',                         strategy.add_evalorga,    name='commercial__add_evaluated_orgas'),
    url(r'^strategy/(?P<strategy_id>\d+)/add/organisation[/]?$',                         strategy.EvaluatedOrgaAdding.as_view(), name='commercial__add_evaluated_orgas'),
    url(r'^strategy/(?P<strategy_id>\d+)/organisation/delete[/]?$',                      strategy.delete_evalorga,               name='commercial__remove_evaluated_orga'),
    # url(r'^strategy/(?P<strategy_id>\d+)/organisation/(?P<orga_id>\d+)/evaluation[/]?$', strategy.orga_evaluation, name='commercial__orga_evaluation'),
    url(r'^strategy/(?P<strategy_id>\d+)/organisation/(?P<orga_id>\d+)/evaluation[/]?$', strategy.OrgaEvaluation.as_view(),      name='commercial__orga_evaluation'),
    # url(r'^strategy/(?P<strategy_id>\d+)/organisation/(?P<orga_id>\d+)/synthesis[/]?$',  strategy.orga_synthesis,  name='commercial__orga_synthesis'),
    url(r'^strategy/(?P<strategy_id>\d+)/organisation/(?P<orga_id>\d+)/synthesis[/]?$',  strategy.OrgaSynthesis.as_view(),       name='commercial__orga_synthesis'),

    # Scores & category
    url(r'^strategy/(?P<strategy_id>\d+)/set_asset_score[/]?$', strategy.set_asset_score,      name='commercial__set_asset_score'),
    url(r'^strategy/(?P<strategy_id>\d+)/set_charm_score[/]?$', strategy.set_charm_score,      name='commercial__set_charm_score'),
    url(r'^strategy/(?P<strategy_id>\d+)/set_segment_cat[/]?$', strategy.set_segment_category, name='commercial__set_segment_category'),

    # Bricks reloading
    url(r'^bricks/reload/matrix/(?P<strategy_id>\d+)/(?P<orga_id>\d+)[/]?$', strategy.reload_matrix_brick, name='commercial__reload_matrix_brick'),
]


# if not contact_model_is_custom():
#     urlpatterns += [
#         url(r'^salesmen[/]?$',     salesman.listview, name='commercial__list_salesmen'),
#         url(r'^salesman/add[/]?$', salesman.add,      name='commercial__create_salesman'),
#     ]
urlpatterns += swap_manager.add_group(
    contact_model_is_custom,
    Swappable(url(r'^salesmen[/]?$',     salesman.listview,                   name='commercial__list_salesmen')),
    Swappable(url(r'^salesman/add[/]?$', salesman.SalesManCreation.as_view(), name='commercial__create_salesman')),
    app_name='commercial',
).kept_patterns()

# if not act_model_is_custom():
#     urlpatterns += [
#         url(r'^acts[/]?$',                     act.listview,   name='commercial__list_acts'),
#         url(r'^act/add[/]?$',                  act.add,        name='commercial__create_act'),
#         url(r'^act/edit/(?P<act_id>\d+)[/]?$', act.edit,       name='commercial__edit_act'),
#         url(r'^act/(?P<act_id>\d+)[/]?$',      act.detailview, name='commercial__view_act'),
#     ]
urlpatterns += swap_manager.add_group(
    act_model_is_custom,
    Swappable(url(r'^acts[/]?$',                     act.listview,              name='commercial__list_acts')),
    Swappable(url(r'^act/add[/]?$',                  act.ActCreation.as_view(), name='commercial__create_act')),
    Swappable(url(r'^act/edit/(?P<act_id>\d+)[/]?$', act.ActEdition.as_view(),  name='commercial__edit_act'), check_args=Swappable.INT_ID),
    Swappable(url(r'^act/(?P<act_id>\d+)[/]?$',      act.ActDetail.as_view(),   name='commercial__view_act'), check_args=Swappable.INT_ID),
    app_name='commercial',
).kept_patterns()


# if not opportunity_model_is_custom():
#     urlpatterns += [
#         url(r'^act/(?P<act_id>\d+)/add/opportunity[/]?$', act.add_opportunity, name='commercial__create_opportunity'),
#     ]
urlpatterns += swap_manager.add_group(
    opportunity_model_is_custom,
    Swappable(url(r'^act/(?P<act_id>\d+)/add/opportunity[/]?$',
                  act.RelatedOpportunityCreation.as_view(),
                  name='commercial__create_opportunity',
                 ),
              check_args=Swappable.INT_ID,
             ),
    app_name='commercial',
).kept_patterns()

# TODO: a separated file for pattern ???
# if not pattern_model_is_custom():
#     urlpatterns += [
#         url(r'^objective_patterns[/]?$',                            act.listview_objective_pattern,   name='commercial__list_patterns'),
#         url(r'^objective_pattern/add[/]?$',                         act.add_objective_pattern,        name='commercial__create_pattern'),
#         url(r'^objective_pattern/edit/(?P<objpattern_id>\d+)[/]?$', act.edit_objective_pattern,       name='commercial__edit_pattern'),
#         url(r'^objective_pattern/(?P<objpattern_id>\d+)[/]?$',      act.objective_pattern_detailview, name='commercial__view_pattern'),
#     ]
urlpatterns += swap_manager.add_group(
    pattern_model_is_custom,
    Swappable(url(r'^objective_patterns[/]?$',                            act.listview_objective_pattern,            name='commercial__list_patterns')),
    Swappable(url(r'^objective_pattern/add[/]?$',                         act.ActObjectivePatternCreation.as_view(), name='commercial__create_pattern')),
    Swappable(url(r'^objective_pattern/edit/(?P<objpattern_id>\d+)[/]?$', act.ActObjectivePatternEdition.as_view(),  name='commercial__edit_pattern'), check_args=Swappable.INT_ID),
    Swappable(url(r'^objective_pattern/(?P<objpattern_id>\d+)[/]?$',      act.ActObjectivePatternDetail.as_view(),   name='commercial__view_pattern'), check_args=Swappable.INT_ID),
    app_name='commercial',
).kept_patterns()

# if not strategy_model_is_custom():
#     urlpatterns += [
#         url(r'^strategies[/]?$',                         strategy.listview,   name='commercial__list_strategies'),
#         url(r'^strategy/add[/]?$',                       strategy.add,        name='commercial__create_strategy'),
#         url(r'^strategy/edit/(?P<strategy_id>\d+)[/]?$', strategy.edit,       name='commercial__edit_strategy'),
#         url(r'^strategy/(?P<strategy_id>\d+)[/]?$',      strategy.detailview, name='commercial__view_strategy'),
#     ]
urlpatterns += swap_manager.add_group(
    strategy_model_is_custom,
    Swappable(url(r'^strategies[/]?$',                         strategy.listview,                   name='commercial__list_strategies')),
    Swappable(url(r'^strategy/add[/]?$',                       strategy.StrategyCreation.as_view(), name='commercial__create_strategy')),
    Swappable(url(r'^strategy/edit/(?P<strategy_id>\d+)[/]?$', strategy.StrategyEdition.as_view(),  name='commercial__edit_strategy'), check_args=Swappable.INT_ID),
    Swappable(url(r'^strategy/(?P<strategy_id>\d+)[/]?$',      strategy.StrategyDetail.as_view(),   name='commercial__view_strategy'), check_args=Swappable.INT_ID),
    app_name='commercial',
).kept_patterns()
