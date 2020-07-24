
(function($) {
    "use strict";

    window.QUnitMixin = function() {
        var self = this;
        var reserved = ['setup', 'teardown', 'beforeEach', 'afterEach'];
        var mixins = this.__mixins = [QUnitBaseMixin].concat(Array.copy(arguments));

        mixins.forEach(function(mixin) {
            for (var key in mixin) {
                if (reserved.indexOf(key) === -1) {
                    self[key] = mixin[key];
                }
            }
        });
    };

    QUnitMixin.prototype = {
        beforeEach: function() {
            var self = this;

            this.__mixins.forEach(function(mixin) {
                if (Object.isFunc(mixin.beforeEach)) {
                    mixin.beforeEach.call(self);
                }
            });
        },

        afterEach: function(env) {
            var self = this;

            this.__mixins.forEach(function(mixin) {
                if (Object.isFunc(mixin.afterEach)) {
                    mixin.afterEach.call(self, env);
                }
            });
        }
    };

    window.QUnitBaseMixin = {
        assertRaises: function(block, expected, message) {
            QUnit.assert.raises(block,
                   function(error) {
                        ok(error instanceof expected, 'error is ' + expected);
                        equal(message, '' + error);
                        return true;
                   });
        },

        assertNoXSS: function(block) {
            // Theses scripts are inspired by those found here:
            // https://owasp.org/www-community/xss-filter-evasion-cheatsheet
            var scripts = [
                '<script>QUnit.pushFailure("XSS < script>...< /script>");</script>',
                '<img src="javascript:QUnit.pushFailure(\'XSS < img src=...>\')" />',
                '<img src=/ onerror="QUnit.pushFailure(\'XSS < img onerror=...>\')"></img>',
                '\<a data-test="qunitXSS" onmouseover="QUnit.pushFailure(\'XSS < a mouseover=...>\')"\>xxs link\</a\>',
            ];

            scripts.forEach(function(script) {
                var success = false;

                try {
                    block.bind(this)(script);
                    success = true;
                } finally {
                    ok(success, 'XSS test as failed. See logs for stacktrace.');
                }

                // Trigger events for some XSS issues
                $('[data-test="qunitXSS"]').mouseover().click();
            }.bind(this));
        },

        equalHtml: function(expected, element, message) {
            QUnit.assert.equal($('<div>').append(expected).html(), $(element).html(), message);
        },

        equalOuterHtml: function(expected, element, message) {
            QUnit.assert.equal($('<div>').append(expected).html(), $('<div>').append($(element).clone()).html(), message);
        }
    };

    window.QUnitConsoleMixin = {
        beforeEach: function() {
            this.resetMockConsoleWarnCalls();

            var self = this;
            var __consoleWarn = this.__consoleWarn = console.warn;
            var __consoleError = this.__consoleError = console.error;

            console.warn = function() {
                var args = Array.copy(arguments);
                self.__consoleWarnCalls.push(args);
                return __consoleWarn.apply(this, args);
            };

            console.error = function() {
                var args = Array.copy(arguments);
                self.__consoleErrorCalls.push(args);
                return __consoleError.apply(this, args);
            };
        },

        afterEach: function() {
            console.warn = this.__consoleWarn;
            console.error = this.__consoleError;
        },

        mockConsoleWarnCalls: function() {
            return this.__consoleWarnCalls;
        },

        resetMockConsoleWarnCalls: function() {
            this.__consoleWarnCalls = [];
        },

        mockConsoleErrorCalls: function() {
            return this.__consoleWarnCalls;
        },

        resetMockConsoleErrorCalls: function() {
            this.__consoleWarnCalls = [];
        }
    };
}(jQuery));
