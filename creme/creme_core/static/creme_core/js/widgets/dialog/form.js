/*******************************************************************************
    Creme is a free/open-source Customer Relationship Management software
    Copyright (C) 2009-2016  Hybird

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

/*
 * Requires : creme.utils
 */

(function($) {
"use strict";

creme.dialog = creme.dialog || {};

creme.dialog.FormDialog = creme.dialog.Dialog.sub({
    _init_: function(options) {
        var self = this;

        options = $.extend({
            autoFocus: true,
            submitOnKey: 13,
            submitData: {},
            noValidate: false,
            validator: 'default'
        }, options || {});

        this._super_(creme.dialog.Dialog, '_init_', options);

        if (Object.isFunc(options.validator)) {
            this.validator(options.validator);
        } else if (options.validator === 'innerpopup') {
            this.validator(this._compatibleValidator);
        } else {
            this.validator(this._defaultValidator);
        }

        var disable_buttons = function() {
            self._updateButtonState("send", false);
            self._updateButtonState("cancel", true, false);
        };

        this.frame().on('before-submit before-fetch', disable_buttons);

        this._submitListeners = {
            'submit-done': this._onSubmitDone.bind(this),
            'submit-fail': this._onSubmitFail.bind(this)
        };

        this._submitKeyCb = this._onSubmitKey.bind(this);
    },

    validator: function(validator) {
        if (validator === undefined) {
            return this._validator;
        }

        if (!Object.isFunc(validator)) {
            throw new Error('validator is not a function');
        }

        this._validator = validator;
        return this;
    },

    _defaultValidator: function(data, statusText, dataType) {
        return !creme.utils.isHTMLDataType(dataType) || data.match(/<form[^>]*>/) === null;
    },

    _compatibleValidator: function(data, statusText, dataType) {
        if (Object.isEmpty(data) || !creme.utils.isHTMLDataType(dataType)) {
            return true;
        }

        if (data.match(/^<div[^>]+class="in-popup"[^>]*>/)) {
            if (data.match(/^<div[^>]+closing="true"[^>]*>/)) {
                return true;
            }

            return (data.match(/<form[^>]*>/) === null);
        }

        return false;
    },

    _validate: function(data, statusText, dataType) {
        var validator = this.validator();
        return !Object.isFunc(validator) || validator(data, statusText, dataType);
    },

    _frameSubmitData: function(data) {
        var options = this.options;
        var submitData = Object.isFunc(options.submitData) ? options.submitData.bind(this)(options, data) : options.submitData || {};
        return $.extend({}, submitData, data);
    },

    form: function() {
        return $('form:first', this.content());
    },

    submit: function(options, data, listeners) {
        options = options || {};

        var form = this.form();
        var errors = creme.forms.validateHtml5Form(form, this.options);

        if (Object.isEmpty(errors) === false) {
            return this;
        }

        data = Object.isFunc(data) ? data.bind(this)(options) : data;
        var submitData = this._frameSubmitData(data);

        this.frame().submit('', $.extend({}, options, {data: submitData}), form, this._submitListeners);
        return this;
    },

    _onFrameCleanup: function() {
        this._super_(creme.dialog.Dialog, '_onFrameCleanup');
        this.frame().delegate().off('keypress', this._submitKeyCb);
    },

    _onFrameUpdate: function(event, data, dataType, action) {
        if (action !== 'submit') {
            this._super_(creme.dialog.Dialog, '_onFrameUpdate', event, data, dataType, action);
        }

        var content = this.frame().delegate();

        if (this.options.autoFocus) {
            var autofocus = $('[autofocus]:tabbable:first', content);

            if (autofocus.length > 0) {
                autofocus.focus();
            } else {
                $(':tabbable:first', content).focus();
            }
        } else {
            $(':tabbable', content).blur();
        }

        if (this.options.submitOnKey) {
            content.on('keypress', this._submitKeyCb);
        }
    },

    _onSubmitDone: function(event, data, statusText, dataType) {
        if (this._validate(data, statusText, dataType)) {
            this._destroyDialog();
            this._events.trigger('form-success', [data, statusText, dataType], this);
            return;
        }

        this._super_(creme.dialog.Dialog, '_onFrameUpdate', event, data, dataType, 'submit');
        this._updateButtonState("send", true, 'auto');
        this._updateButtonState("cancel", true);

        this._events.trigger('form-error', [data, statusText, dataType], this);
    },

    _onSubmitFail: function(event, data, statusText) {
        this._updateButtonState("send", false);
        this._updateButtonState("cancel", true, true);
    },

    _onSubmitKey: function(e) {
        if (e.keyCode === this.options.submitOnKey && $(e.target).is(':not(textarea)')) {
            e.preventDefault();
            this.button('send').click();
        }
    },

    _onOpen: function(dialog, frame, options) {
        var self = this;

        frame.onFetchFail(function(data, status) {
                  self._updateButtonState("send", false);
                  self._updateButtonState("cancel", true, true);
              })
              .onFetchDone(function(data, status) {
                  self._updateButtonState("send", true, 'auto');
                  self._updateButtonState("cancel", true);
              });

        this._super_(creme.dialog.Dialog, '_onOpen', dialog, frame, options);
    },

    _frameActionFormSubmitButtons: function(options) {
        var self = this;
        var buttons = {};
        var buttonIds = {};
        var submitCb = function(button, e, options) {
            options = $.extend({
                noValidate: button.is('[novalidate]')
            }, options || {});

            this.submit(options, options.data);
        };
        var buildUniqueButtonId = function(id) {
            var suffix = buttonIds[id] || 0;
            buttonIds[id] = suffix + 1;

            return (suffix > 0) ? id + '-' + suffix : id;
        };

        $('.ui-creme-dialog-action[type="submit"]', this.content()).each(function() {
            var item  = $(this);
            var data  = {};
            var name  = item.attr('name');
            var label = item.text();
            var order = parseInt(item.attr('data-dialog-action-order') || 0);
            var value = item.val();
            var id = buildUniqueButtonId(name || 'send');

            if (item.is('input')) {
                label = value || gettext('Save');
            } else {
                label = label || gettext('Save');

                if (!Object.isEmpty(name) && !Object.isNone(value)) {
                    data[name] = value;
                }
            }

            self._appendButton(buttons, id, label, submitCb,
                               {data: data, order: order});
        }).toggleAttr('disabled', true);

        if (Object.isEmpty(buttons)) {
            this._appendButton(buttons, 'send', gettext('Save'), submitCb);
        }

        return buttons;
    },

    _frameActionButtons: function(options) {
        var buttons = this._super_(creme.dialog.Dialog, '_frameActionButtons', options);
        $.extend(buttons, this._frameActionFormSubmitButtons(options));
        return buttons;
    },

    _defaultButtons: function(buttons, options) {
        this._appendButton(buttons, 'cancel', gettext('Cancel'), function(button, e, options) {
                               this.close();
                           });

        return buttons;
    },

    onFormSuccess: function(success) {
        this._events.bind('form-success', success);
        return this;
    },

    onFormError: function(error) {
        this._events.bind('form-error', error);
        return this;
    }
});

creme.dialog.FormDialogAction = creme.component.Action.sub({
    _init_: function(options, listeners) {
        this._super_(creme.component.Action, '_init_', this._openPopup, options);
        this._listeners = listeners || {};
    },

    _onSubmit: function(event, data, statusText, dataType) {
        if ($.matchIEVersion(7, 8, 9)) {
            data = data.endsWith('</json>') || data.endsWith('</JSON>') ? data.substr(0, data.length - '</json>'.length) : data;
            dataType = 'text/json';
        }

        this.done(data, dataType);
    },

    _buildPopup: function(options) {
        var self = this;
        options = $.extend(this.options(), options || {});

        return new creme.dialog.FormDialog(options).onFormSuccess(this._onSubmit.bind(this))
                                                   .onClose(function() {
                                                        self.cancel();
                                                    })
                                                   .on(this._listeners);
    },

    _openPopup: function(options) {
        this._buildPopup(options).open();
    }
});
}(jQuery));
