/*******************************************************************************
    Creme is a free/open-source Customer Relationship Management software
    Copyright (C) 2009-2018  Hybird

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*******************************************************************************/

(function($) {
    "use strict";

creme.lv_widget = {};

// TODO: beware it won't work from a Popover element with would be displayed in a popup list-view
//       (because popovers are detached from their original root in the DOM)
//       It should be fixed with the new action system like the bricks' one.
creme.lv_widget.findList = function(element) {
    var container = $(element).parents('.ui-dialog:first');

    if (container.length === 0) {
        container = $('body');
    }

    return container.find('form.ui-creme-listview:first');
};

creme.lv_widget.deleteFilter = function(list, filter_id, url) {
    return creme.utils.confirmPOSTQuery(url, {}, {id: filter_id})
                      .onDone(function(event, data) {
                          list.list_view('reload');
                       })
                      .start();
};

creme.lv_widget.selectedLines = function(list) {
    list = $(list);

    if (list.list_view('countEntities') === 0) {
        return [];
    }

    return list.list_view('getSelectedEntitiesAsArray');
};

creme.lv_widget.DeleteSelectedAction = creme.component.Action.sub({
    _init_: function(list, options) {
        this._super_(creme.component.Action, '_init_', this._run, options);
        this._list = list;
    },

    _onDeleteFail: function(event, error, data) {
        var self = this;
        var list = this._list;

        var message = Object.isType(error, 'string') ? error : (error.message || gettext("Error"));
        var header = creme.ajax.localizedErrorMessage(data);
        var parser = new creme.utils.JSON();

        if (!Object.isEmpty(message) && parser.isJSON(message)) {
            var results = parser.decode(message);
            var removed_count = results.count - results.errors.length;

            header = '';

            if (removed_count > 0) {
                header = ngettext('%d entity have been deleted.',
                                  '%d entities have been deleted.',
                                  removed_count).format(removed_count);
            }

            if (results.errors) {
                header += ngettext(' %d entity cannot be deleted.',
                                   ' %d entities cannot be deleted.',
                                   results.errors.length).format(results.errors.length);
            }

            message = '<ul>' + results.errors.map(function(item) {
                                                 return '<li>' + item + '</li>';
                                              }).join('') +
                      '</ul>';
        }

        creme.dialogs.warning(message, {header: header})
                     .onClose(function() {
                          list.reload();
                          self.fail();
                      })
                     .open();
    },

    _run: function(options) {
        options = $.extend({}, this.options(), options || {});

        var self = this;
        var list = this._list;
        var selection = creme.lv_widget.selectedLines(list);

        if (selection.length < 1) {
            creme.dialogs.warning(gettext("Please select at least one entity."))
                         .onClose(function() {
                             self.cancel();
                          })
                         .open();
        } else {
            var query = creme.utils.confirmPOSTQuery(options.url, {warnOnFail: false, dataType: 'json'}, {ids: selection.join(',')});
            query.onFail(this._onDeleteFail.bind(this))
                 .onCancel(function(event, data) {
                     self.cancel();
                  })
                 .onDone(function(event, data) {
                     list.reload();
                     self.done();
                  })
                 .start();
        }
    }
});

creme.lv_widget.AddToSelectedAction = creme.component.Action.sub({
    _init_: function(list, options) {
        this._super_(creme.component.Action, '_init_', this._run, options);
        this._list = list;
    },

    _run: function(options) {
        options = $.extend({}, this.options(), options || {});

        var self = this;
        var list = this._list;
        var selection = creme.lv_widget.selectedLines(list);

        if (selection.length < 1) {
            creme.dialogs.warning(gettext("Please select at least one entity."))
                         .onClose(function() {
                             self.cancel();
                          })
                         .open();
        } else {
            var dialog = creme.dialogs.form(options.url, {
                                                submitData: {ids: selection}
                                            }, {
                                                ids: selection
                                            });

            dialog.onFormSuccess(function(event, data) {
                       list.reload();
                       self.done();
                   })
                   .onClose(function() {
                       self.cancel();
                   })
                   .open({width: 800});
        }
    }
});

creme.lv_widget.EditSelectedAction = creme.component.Action.sub({
    _init_: function(list, options) {
        this._super_(creme.component.Action, '_init_', this._run, options);
        this._list = list;
    },

    _run: function(options) {
        options = $.extend({}, this.options(), options || {});

        var self = this;
        var list = this._list;
        var selection = creme.lv_widget.selectedLines(list);

        if (selection.length < 1) {
            creme.dialogs.warning(gettext("Please select at least one entity."))
                         .onClose(function() {
                             self.cancel();
                          })
                         .open();
        } else {
            var dialog = creme.dialogs.form(options.url, {submitData: {entities: selection}});

            dialog.onFormSuccess(function(event, data) {
                       list.reload();
                       self.done();
                   })
                   .onFormError(function(event, data) {
                       if ($('form', this.content()).length === 0) {
                           this._updateButtonState('send', false);
                           this._updateButtonLabel('cancel', gettext('Close'));
                           this._bulk_edit_done = true;
                       }
                   })
                   .onClose(function() {
                       if (this._bulk_edit_done) {
                           list.reload();
                           self.done();
                       } else {
                           self.cancel();
                       }
                   })
                   .on('frame-update', function(event, frame) {
                       var summary = $('.bulk-selection-summary', frame.delegate());

                       if (summary.length) {
                           var count = selection.length;
                           var message = summary.attr('data-msg') || '';
                           var plural = summary.attr('data-msg-plural');

                           if (pluralidx(count)) {
                               message = plural || message;
                           }

                           // TODO: need all model select_label in djangojs.po files
                           // var content = ngettext(summary.attr('data-msg'), summary.attr('data-msg-plural'), count);
                           summary.text(message.format(selection.length));
                       }
                   })
                   .open({width: 800});
        }
    }
});

creme.lv_widget.MergeSelectedAction = creme.component.Action.sub({
    _init_: function(list, options) {
        this._super_(creme.component.Action, '_init_', this._run, options);
        this._list = list;
    },

    _run: function(options) {
        options = $.extend({}, this.options(), options || {});

        var self = this;
        var list = this._list;
        var selection = creme.lv_widget.selectedLines(list);

        if (selection.length !== 2) {
            creme.dialogs.warning(gettext("Please select 2 entities."))
                         .onClose(function() {
                             self.cancel();
                          })
                         .open();
        } else {
            try {
                creme.utils.goTo(options.url + '?' + $.param({id1: selection[0], id2: selection[1]}));
            } catch (e) {
                this.fail(e);
            }
        }
    }
});

creme.lv_widget.handleSort = function(sort_field, sort_order, new_sort_field, input, callback) {
    var $sort_field = $(sort_field);
    var $sort_order = $(sort_order);

    if ($sort_field.val() === new_sort_field) {
        if ($sort_order.val() === '') {
            $sort_order.val('-');
        } else {
            $sort_order.val('');
        }
    } else {
        $sort_order.val('');
    }

    $sort_field.val(new_sort_field);

    if (Object.isFunc(callback)) {
        callback(input);
    }
};

creme.lv_widget.initialize = function(options, listview) {
    var submit_handler, history_handler;
    var dialog = listview.parents('.ui-dialog-content:first');
    var submit_url = options.reloadurl || window.location.pathname;
    var id = dialog.length > 0 ? dialog.attr('id') : undefined;

    if (id) {
        submit_handler = function(input, extra_data) {
            extra_data = id ? $.extend({whoami: id}, extra_data) : extra_data;
            var submit_options = {
                    action: submit_url,
                    success: function(event, data, status) {
                        data = id ? data + '<input type="hidden" name="whoami" value="' + id + '"/>' : data;
                        creme.widget.destroy(listview);
                        listview.html(data);
                        creme.widget.create(listview);
                    }
                };

            listview.list_view('setReloadUrl', submit_url);
            listview.list_view('handleSubmit', submit_options, input, extra_data);
        };
    } else {
        history_handler = function(url) {
            creme.history.push(url);
        };
        submit_handler = function(input, extra_data) {
            var submit_options = {
                    action: submit_url,
                    success: function(event, data, status) {
                        creme.widget.destroy(listview);
                        listview.html(data);
                        creme.widget.create(listview);
                    }
                };

            listview.list_view('handleSubmit', submit_options, input, extra_data);
        };
    }

    listview.list_view({
        o2m:              options.multiple ? 0 : 1,
        historyHandler:   history_handler,
        submitHandler:    submit_handler,
        kd_submitHandler: function (e, input, extra_data) {
            e = (window.event) ? window.event : e;
            var key = (window.event) ? e.keyCode : e.which;

            if (key === 13) {
                listview.list_view('getSubmit')(input, extra_data);
            }

            return true;
        }
    });

    listview.list_view('setReloadUrl', submit_url);
};

creme.lv_widget.listViewAction = function(url, options, data) {
    options = options || {};

    var selector = function(dialog) {
        return creme.lv_widget.selectedLines($('.ui-creme-listview', dialog)) || [];
    };

    var validator = function(data) {
          if (Object.isEmpty(data)) {
              creme.dialogs.warning(gettext('Please select at least one entity.'), {'title': gettext("Error")}).open();
              return false;
          }

          if (!options.multiple && data.length > 1) {
              creme.dialogs.warning(gettext('Please select only one entity.'), {'title': gettext("Error")}).open();
              return false;
          }

          return true;
    };

    return creme.utils.innerPopupFormAction(url, {
               submit_label: gettext("Validate the selection"),
               submit: selector,
               validator: validator,
               closeOnEscape: options.closeOnEscape
           }, data);
};


creme.lv_widget.ListViewActionBuilders = creme.action.ActionBuilderRegistry.sub({
    _init_: function(list) {
        this._list = list;
        this._super_(creme.action.ActionBuilderRegistry, '_init_');
    },

    _defaultDialogOptions: function(url, title) {
        var width = $(window).innerWidth();

        return {
            resizable: true,
            draggable: true,
            width: width * 0.8,
            maxWidth: width,
            url: url,
            title: title,
            validator: 'innerpopup'
        };
    },

    _build_update: function(url, options, data, e) {
        var list = this._list;
        var action;
        options = $.extend({action: 'post'}, options || {});

        if (options.confirm) {
            action = creme.utils.confirmAjaxQuery(url, options, data);
        } else {
            action = creme.utils.ajaxQuery(url, options, data);
        }

        return action.onDone(function() {
            list.reload();
        });
    },

    _build_delete: function(url, options, data, e) {
        return this._build_update(url, $.extend({}, options, {
            confirm: gettext('Are you sure ?')
        }), data, e);
    },

    _build_form: function(url, options, data, e) {
        var list = this._list;

        options = $.extend(this._defaultDialogOptions(url), options || {});

        return new creme.dialog.FormDialogAction(options, {
            'form-success': function() {
                list.reload();
             }
        });
    },

    _build_clone: function(url, options, data, e) {
        options = $.extend({
            action: 'post',
            confirm: gettext('Do you really want to clone this entity?')
        }, options || {});

        var action = creme.utils.confirmAjaxQuery(url, options, data);
        action.onDone(function(event, data, xhr) {
            creme.utils.goTo(data);
        });

        return action;
    },

    _build_edit_selection: function(url, options, data, e) {
        return new creme.lv_widget.EditSelectedAction(this._list, {url: url});
    },

    _build_delete_selection: function(url, options, data, e) {
        return new creme.lv_widget.DeleteSelectedAction(this._list, {url: url});
    },

    _build_addto_selection: function(url, options, data, e) {
        return new creme.lv_widget.AddToSelectedAction(this._list, {url: url});
    },

    _build_merge_selection: function(url, options, data, e) {
        return new creme.lv_widget.MergeSelectedAction(this._list, {url: url});
    },

    _build_redirect: function(url, options, data) {
        var context = {
            location: window.location.href.replace(/.*?:\/\/[^\/]*/g, '') // remove 'http://host.com'
        };

        return new creme.component.Action(function() {
            creme.utils.goTo(creme.utils.templatize(url, context).render());
        });
    }
});

creme.lv_widget.ListViewHeader = creme.component.Component.sub({
    _init_: function(options) {
        options = $.extend({
            standalone: false,
            headTop: 0
        }, options || {});

        this._isStandalone = options.standalone;
        this._headTop = options.headTop;

        this._rowListeners = {
            mouseenter: this._onEnterSelectableRow.bind(this),
            mouseleave: this._onLeaveSelectableRow.bind(this),
            selection: this._onRowSelectionChange.bind(this)
        };
        this._floatListeners = {
            floatHead: this._onHeadFloatEnabled.bind(this)
        };
        this._documentListeners = {
            scroll: this._onDocumentScroll.bind(this)
        };
    },

    isBound: function() {
        return this._list !== undefined;
    },

    _onEnterSelectableRow: function(e) {
        this._list.addClass('first-row-hovered');

        if (this._isStandalone) {
            $('.listview.floatThead-table').addClass('first-row-hovered');
        }
    },

    _onLeaveSelectableRow: function(e) {
        this._list.removeClass('first-row-hovered');

        if (this._isStandalone) {
            $('.listview.floatThead-table').removeClass('first-row-hovered');
        }
    },

    _onRowSelectionChange: function(e, data) {
        this._list.toggleClass('first-row-selected', data.selected);

        if (this._isStandalone) {
            $('.listview.floatThead-table').toggleClass('first-row-selected', data.selected);
        }
    },

    _onHeadFloatEnabled: function(e, isFloated, container) {
        if (isFloated) {
            container.addClass('floated');
            this._list.addClass('floated');

            // vertical constraint 2 : close header actions popovers when they would collide with the floating header scrolling
            $('.header-actions-popover').trigger('modal-close');
        } else {
            container.removeClass('floated');
            this._list.removeClass('floated');
        }
    },

    _onDocumentScroll: function(e) {
        this.updateAnchorPosition();
    },

    bind: function(list) {
        if (this.isBound()) {
            throw new Error('ListViewHeader is already bound');
        }

        var isStandalone = this._isStandalone;
        var headTop = this._headTop;
        this._list = list;

        // handle selection and hover border on floating header so that the first row is correctly styled
        this._list.on('mouseenter', 'tr.selectable:first-child', this._rowListeners.mouseenter);
        this._list.on('mouseleave', 'tr.selectable:first-child', this._rowListeners.mouseleave);
        this._list.on('row-selection-changed', 'tbody tr:first-child', this._rowListeners.selection);

        // listview-popups have no floatThead, stickiness, vertical constraints etc
        if (isStandalone) {
            list.floatThead({
                top: headTop,
                zIndex: 97, // under the popups overlays, under the popovers and their glasspanes
                scrollContainer: function (table) {
                    return table.closest('.sub_content');
                }
            });

            var floatContainer = $('.floatThead-container');
            var isFloating = $(document).scrollTop() > list.offset().top;

            // when the page is loaded and the scrollbar is already scrolled past the header, notify it is already floated
            if (isFloating) {
                floatContainer.addClass('floated');
                list.addClass('floated');
            }

            // or when the floatThead script floats it automatically
            list.on('floatThead', this._floatListeners.floatHead);

            // the anchor will hold the header shadow
            var anchor = this._floatAnchor = $('<div class="floated-header-anchor">');
            anchor.insertAfter(floatContainer)
                  .css({
                      'position': 'fixed'
                  });

            this.updateAnchorPosition();

            $(document).on('scroll', this._documentListeners.scroll);
        }

        return this;
    },

    unbind: function() {
        if (this.isBound() === false) {
            throw new Error('ListViewHeader is not bound');
        }

        this._list.off('mouseenter', 'tr.selectable:first-child', this._rowListeners.mouseenter);
        this._list.off('mouseleave', 'tr.selectable:first-child', this._rowListeners.mouseleave);
        this._list.off('row-selection-changed', 'tbody tr:first-child', this._rowListeners.selection);

        if (this._isStandalone) {
            this._floatAnchor.detach();
            this._list.off('floatThead', this._floatListeners.floatHead);
            $(document).on('scroll', this._documentListeners.scroll);
        }

        this._floatAnchor = undefined;
        this._list = undefined;

        return this;
    },

    updateAnchorPosition: function() {
        if (this._isStandalone) {
            var scrollLeft = $(document).scrollLeft();
            var viewportWidth = $(window).width();

            // complex stickiness between two absolute values modeled as position: fixed over the viewport
            var listAnchorStickingStart = this._list.offset().left;
            var listAnchorStickingEnd = listAnchorStickingStart + this._list.width();

            var overShooting = scrollLeft + viewportWidth >= listAnchorStickingEnd;
            var overshoot = Math.abs(Math.ceil(listAnchorStickingEnd - viewportWidth - scrollLeft));

            var floatContainer = $('.floatThead-container');
            var headerHeight = $(floatContainer.children().get(0)).height(); // we use the height of the contained table because it excludes its own padding
            var anchorHeight = this._floatAnchor.height();

            this._floatAnchor.css({
                'left': Math.max(0, listAnchorStickingStart - scrollLeft),
                'right': overShooting ? overshoot : 0,
                // NB it would be great if we could get the bottom of '.floatThead-container' & set the same bottom to the anchor...
                // 'top': 35 /* menu height */ + $('.floatThead-container').innerHeight() - 4 /* padding + borders */ - 10 /* shadow height */
                'top': this._headTop + headerHeight - anchorHeight
            });
        }
    }
});

creme.lv_widget.ListViewLauncher = creme.widget.declare('ui-creme-listview', {
    options: {
        multiple:     false,
        whoami:       '',
        'reload-url': ''
    },

    _destroy: function(element) {
        $(document).off('scroll', this._scrollListener);
        element.removeClass('widget-ready');
    },

    _create: function(element, options, cb, sync, args) {
        var multiple = element.is('[multiple]') || options.multiple;
        var list = this._list = element.find('.listview');

        this._isStandalone = list.hasClass('listview-standalone');
        this._pager = new creme.list.Pager();
        this._header = new creme.lv_widget.ListViewHeader({
            standalone: this._isStandalone,
            headTop: $('.header-menu').height()
        });

        this._rowCount = parseInt(list.attr('data-total-count'));
        this._rowCount = isNaN(this._rowCount) ? 0 : this._rowCount;

        this._scrollListener = this._onDocumentScroll.bind(this);

        // handle popup differentiation
        if (this._isStandalone) {
            element.addClass('ui-creme-listview-standalone');
            $(document).on('scroll', this._scrollListener);
            this._handleHorizontalStickiness();
        } else {
            element.addClass('ui-creme-listview-popup');
        }

        // Only init the $.fn.list_view once per form, not on every listview reload
        if (!element.data('list_view')) {
            creme.lv_widget.initialize({
                multiple:  multiple,
                reloadurl: options['reload-url']
            }, element);
        }

        // only hook up list behavior when there are rows
        if (this._rowCount > 0) {
            if (!this._isStandalone) {
                // pagination in popups
                var popup = element.parents('.ui-dialog').first();
                list.find('.list-footer-container').css('max-width', popup.width());
            } else {
                // left/right in standalone mode
                this._handleHorizontalStickiness();
            }

            this._header.bind(list);
            this._pager.on('refresh', function(event, page) {
                            element.data('list_view').getSubmit()(null, {page: page});
                        })
                       .bind(list.find('.listview-pagination'));
        }
    },

    _onDocumentScroll: function(e) {
        this._handleHorizontalStickiness();
        this._handleActionPopoverConstraints();
    },

    _handleHorizontalStickiness: function() {
        var scrollLeft = $(document).scrollLeft();
        // Simple stickiness to left: 0
        $('.sticky-container-standalone .sticks-horizontally, .listview-standalone .sticks-horizontally, .footer, .page-decoration').css('transform', 'translateX(' + scrollLeft + 'px)');
    },

    _handleActionPopoverConstraints: function() {
        $('.listview-actions-popover').each(function() {
            var popover = $(this);
            var offset = popover.offset();

            var floatContainer = $('.floatThead-container');
            var floatingOffset = floatContainer.offset();

            // Check for collisions
            if (offset.top < floatingOffset.top + floatContainer.innerHeight() + 5/* safe zone */) {
                var isRowPopover = popover.hasClass('row-actions-popover');
                var isHeaderPopover = popover.hasClass('header-actions-popover');
                var containerIsFloating = floatContainer.hasClass('floated');

                // Vertical constraint 1 : close row actions popovers when they collide with the floating header
                // Vertical constraint 3 : close header actions popovers when they are opened while the header is floating, and the document is scrolled
                var popoverNeedsClosing = isRowPopover || (isHeaderPopover && containerIsFloating);
                if (popoverNeedsClosing) {
                    popover.trigger('modal-close');
                }
            }
        });
    },

    isStandalone: function(element) {
        return this._isStandalone;
    },

    count: function(element) {
        return this._rowCount;
    },

    header: function(element) {
        return this._header;
    },

    pager: function(element) {
        return this._pager;
    },

    controller: function(element) {
        return element.data('list_view');
    }
});

}(jQuery));
