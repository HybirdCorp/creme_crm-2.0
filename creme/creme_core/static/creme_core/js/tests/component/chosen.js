QUnit.module("creme.chosen.js", {
    setup: function() {
        this.resetMockCalls();
        this.anchor = $('<div style="display: none;"></div>').appendTo($('body'));
    },

    teardown: function() {
        this.anchor.detach();
        $('.chzn-drop').detach();
    },

    resetMockCalls: function() {
        this._eventListenerCalls = {};
    },

    mockListenerCalls: function(name) {
        if (this._eventListenerCalls[name] === undefined)
            this._eventListenerCalls[name] = [];

        return this._eventListenerCalls[name];
    },

    mockListener: function(name) {
        var self = this;
        return (function(name) {return function() {
            self.mockListenerCalls(name).push(Array.copy(arguments));
        }})(name);
    },

    assertRaises: function(block, expected, message) {
        QUnit.assert.raises(block,
               function(error) {
                    ok(error instanceof expected, 'error is ' + expected);
                    equal(message, '' + error);
                    return true;
               });
    },

    createSelect: function(options) {
        options = options || [];

        var select = $('<select></select>').appendTo(this.anchor);
        var add = this.addSelectOption.bind(this);

        options.forEach(function(option) {
            add(select, option);
        });

        return select;
    },

    addSelectOption: function(select, option) {
        select.append('<option value="${value}" ${disabled} ${selected}>${label}</option>'.template({
            value: option.value,
            label: option.label,
            disabled: option.disabled ? 'disabled' : '',
            selected: option.selected ? 'selected' : ''
        }));
    }
});

QUnit.test('creme.component.Chosen.activate (empty)', function() {
    var select = this.createSelect();
    var chosen = new creme.component.Chosen();

    equal(false, select.is('.chzn-select'));
    equal(false, chosen.isActive());
    equal(undefined, chosen.element);

    chosen.activate(select);

    equal(true, select.is('.chzn-select'));
    equal(true, chosen.isActive());
    equal(select, chosen.element);
});

QUnit.test('creme.component.Chosen.activate (already activated)', function() {
    var select = this.createSelect([{value: 1, label: 'A'}]);
    var chosen = new creme.component.Chosen();

    chosen.activate(select);

    this.assertRaises(function() {
        chosen.activate(select);
    }, Error, 'Error: Chosen component is already active');
});


QUnit.test('creme.component.Chosen.activate (single)', function() {
    var select = this.createSelect([{value: 5, label: 'E', selected: true}, {value: 1, label: 'A'}]);
    var chosen = new creme.component.Chosen();

    chosen.activate(select);
    equal('E', select.parent().find('.chzn-single span').text());
});

QUnit.test('creme.component.Chosen.activate (multiple)', function() {
    var select = this.createSelect([{value: 5, label: 'E', selected: true}, {value: 1, label: 'A', selected: true}]);
    var chosen = new creme.component.Chosen({multiple: true});

    select.attr('multiple', '');
    select.val([5, 1]);

    chosen.activate(select);
    equal(2, select.parent().find('ul.chzn-choices .search-choice').length);
    equal(0, select.parent().find('ul.chzn-choices.ui-sortable').length); // not sortable
});

QUnit.test('creme.component.Chosen.activate (multiple, sortable)', function() {
    var select = this.createSelect([{value: 5, label: 'E', selected: true}, {value: 1, label: 'A', selected: true}]);
    var chosen = new creme.component.Chosen({multiple: true, sortable: true});

    select.attr('multiple', '');
    select.val([5, 1]);

    chosen.activate(select);

    equal(2, select.parent().find('ul.chzn-choices .search-choice').length);
    equal(1, select.parent().find('ul.chzn-choices.ui-sortable').length); // sortable
});

QUnit.test('creme.component.Chosen.refresh', function() {
    var select = this.createSelect([{value: 5, label: 'E', selected: true}, {value: 1, label: 'A'}]);
    var chosen = new creme.component.Chosen();

    chosen.activate(select);
    equal('E', select.parent().find('.chzn-single span').text());
    equal(2, $('.chzn-drop .chzn-results li').length);

    this.addSelectOption(select, {value: 8, label: 'G'});
    this.addSelectOption(select, {value: 2, label: 'B'});
    this.addSelectOption(select, {value: 3, label: 'C'});

    chosen.refresh();
    equal(5, $('.chzn-drop .chzn-results li').length);
});

QUnit.test('creme.component.Chosen.deactivate', function() {
    var select = this.createSelect([{value: 5, label: 'E', selected: true}, {value: 1, label: 'A'}]);
    var chosen = new creme.component.Chosen();

    chosen.activate(select);

    equal(true, select.is('.chzn-select'));
    equal(true, chosen.isActive());
    equal(select, chosen.element);
    equal('E', select.parent().find('.chzn-single span').text());

    chosen.deactivate(select);

    equal(false, select.is('.chzn-select'));
    equal(false, chosen.isActive());
    equal(undefined, chosen.element);
    equal(0, select.parent().find('.chzn-single span').length);
});

QUnit.test('creme.component.Chosen.deactivate (sortable)', function() {
    var select = this.createSelect([{value: 5, label: 'E', selected: true}, {value: 1, label: 'A'}]);
    var chosen = new creme.component.Chosen({multiple: true, sortable: true});

    select.attr('multiple', '');
    select.val([1, 5]);

    chosen.activate(select);

    equal(true, select.is('.chzn-select'));
    equal(true, chosen.isActive());
    equal(select, chosen.element);
    equal(2, select.parent().find('ul.chzn-choices .search-choice').length);
    equal(1, select.parent().find('ul.chzn-choices.ui-sortable').length); // sortable

    chosen.deactivate(select);

    equal(false, select.is('.chzn-select'));
    equal(false, chosen.isActive());
    equal(undefined, chosen.element);
    equal(0, select.parent().find('ul.chzn-choices').length);
});

QUnit.test('creme.component.Chosen.deactivate (already deactivated)', function() {
    var select = this.createSelect([{value: 5, label: 'E', selected: true}, {value: 1, label: 'A'}]);
    var chosen = new creme.component.Chosen();

    chosen.activate(select);

    equal(true, select.is('.chzn-select'));
    equal(true, chosen.isActive());
    equal('E', select.parent().find('.chzn-single span').text());

    chosen.deactivate(select);
    chosen.deactivate(select);
    chosen.deactivate(select);

    equal(false, select.is('.chzn-select'));
    equal(false, chosen.isActive());
    equal(0, select.parent().find('.chzn-single span').length);
});
