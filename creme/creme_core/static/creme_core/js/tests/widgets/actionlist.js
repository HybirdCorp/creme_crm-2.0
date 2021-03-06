(function($) {

QUnit.module("creme.widget.actionlist.js", new QUnitMixin(QUnitAjaxMixin, QUnitWidgetMixin, {
    buildMockBackend: function() {
        return new creme.ajax.MockAjaxBackend({sync:true, name: 'creme.widget.actionlist.js'});
    },

    beforeEach: function() {
        this.setMockBackendGET({
            'mock/options': this.backend.response(200, [[15, 'a'], [5, 'b'], [3, 'c'], [14, 't'], [42, 'y']]),
            'mock/rtype/1/options': this.backend.response(200, [['rtype.1', 'a'], ['rtype.12', 'b'], ['rtype.3', 'c']]),
            'mock/rtype/5/options': this.backend.response(200, [['rtype.7', 'x'], ['rtype.22', 'y'], ['rtype.3', 'c']]),
            'mock/forbidden': this.backend.response(403, 'HTTP - Error 403'),
            'mock/error': this.backend.response(500, 'HTTP - Error 500')
        });
    },

    afterEach: function() {
        $('.ui-dialog-content').dialog('destroy');
        creme.widget.shutdown($('body'));
    }
}));

function mock_actionlist_create(noauto, options)
{
    var element = creme.widget.buildTag($('<ul/>'), 'ui-creme-actionbuttonlist', options, !noauto)
                       .append($('<li class="delegate"/>'));

    return element;
}

function mock_actionlist_delegate(element, delegate)
{
    $('> li.delegate', element).empty().append(delegate);
}

function mock_actionlist_add(element, options)
{
    var button = creme.widget.writeAttr($('<button type="button"/>').addClass('ui-creme-actionbutton'), options);
    element.append($('<li/>').append(button));
}

function assertAction(action, name, label, type, url, enabled)
{
    equal(Object.isEmpty(action), false, 'action is empty');

    if (Object.isEmpty(action))
        return;

    equal(action.attr('name'), name, 'action name');
    equal(action.attr('label'), label, 'action label');
    equal(action.attr('action'), type, 'action type');
    equal(action.attr('url'), url, 'action url');
    equal(action.is(':not([disabled])'), enabled, 'action disabled ' + name)
}

QUnit.test('creme.widgets.actionlist.create (no delegate, no action)', function(assert) {
    var element = mock_actionlist_create();
    var widget = creme.widget.create(element, {backend: this.backend});

    equal(element.hasClass('widget-active'), true);
    equal(element.hasClass('widget-ready'), true);
    equal(widget.val(), '');
    equal(widget.selector().length, 0);
    equal(widget.actions().length, 0);
    deepEqual(widget.dependencies(), []);
});

QUnit.test('creme.widgets.actionlist.create (no delegate)', function(assert) {
    var element = mock_actionlist_create();
    mock_actionlist_add(element, {name: 'create', label: 'create', url: 'mock/create/popup'});

    var widget = creme.widget.create(element, {backend: this.backend});

    equal(element.hasClass('widget-active'), true);
    equal(element.hasClass('widget-ready'), true);
    equal(widget.val(), '');
    equal(widget.selector().length, 0);
    equal(widget.actions().length, 1);
    deepEqual(widget.dependencies(), []);
});

QUnit.test('creme.widgets.actionlist.create', function(assert) {
    var delegate = this.createDynamicSelectTag();
    this.appendOptionTag(delegate, 'a', 1);
    this.appendOptionTag(delegate, 'b', 5);
    this.appendOptionTag(delegate, 'c', 3);

    var element = mock_actionlist_create();
    mock_actionlist_delegate(element, delegate);
    mock_actionlist_add(element, {name: 'create', label: 'create', url: 'mock/create/popup'});

    var widget = creme.widget.create(element, {backend: this.backend});

    equal(element.hasClass('widget-active'), true);
    equal(element.hasClass('widget-ready'), true);
    equal(widget.selector().length, 1);
    equal(widget.actions().length, 1);

    equal(widget.val(), 1);
    deepEqual(widget.dependencies(), []);

    equal(delegate.hasClass('widget-active'), true);
    equal(delegate.hasClass('widget-ready'), true);

    equal(delegate.creme().widget().val(), 1);
    deepEqual(delegate.creme().widget().dependencies(), []);
});

QUnit.test('creme.widgets.actionlist.create (disabled)', function(assert) {
    var delegate = this.createDynamicSelectTag();
    this.appendOptionTag(delegate, 'a', 1);

    var element = mock_actionlist_create(false, {disabled: ''});
    mock_actionlist_delegate(element, delegate);
    mock_actionlist_add(element, {name: 'create', label: 'create', url: 'mock/create/popup'});

    equal(element.is('[disabled]'), true);
    equal(delegate.is('[disabled]'), false);

    var widget = creme.widget.create(element, {backend: this.backend});

    equal(element.hasClass('widget-ready'), true);
    equal(widget.selector().length, 1);
    equal(widget.actions().length, 1);

    equal(element.is('[disabled]'), true);
    equal(widget.delegate._enabled, false);
    equal(widget.selector().is('[disabled]'), true);
    equal(widget.actions().is('[disabled]'), true);

    var delegate = this.createDynamicSelectTag();
    this.appendOptionTag(delegate, 'a', 1);

    var element = mock_actionlist_create();
    mock_actionlist_delegate(element, delegate);
    mock_actionlist_add(element, {name: 'create', label: 'create', url: 'mock/create/popup'});
    
    equal(element.is('[disabled]'), false);
    equal(delegate.is('[disabled]'), false);

    var widget = creme.widget.create(element, {disabled: true});

    equal(element.hasClass('widget-ready'), true);
    equal(widget.selector().length, 1);
    equal(widget.actions().length, 1);

    equal(element.is('[disabled]'), true);
    equal(widget.delegate._enabled, false);
    equal(widget.selector().is('[disabled]'), true);
    equal(widget.actions().is('[disabled]'), true);
});

QUnit.test('creme.widgets.actionlist.dependencies (url delegate)', function(assert) {
    var delegate = this.createDynamicSelectTag('mock/${ctype}/options', true);

    var element = mock_actionlist_create();
    mock_actionlist_delegate(element, delegate);
    mock_actionlist_add(element, {name: 'create', label: 'create', url: 'mock/create/popup'});

    var widget = creme.widget.create(element, {backend: this.backend});
    deepEqual(delegate.creme().widget().dependencies(), ['ctype']);
    deepEqual(widget.dependencies(), ['ctype']);
});

// TODO : add dependency support for actions
/*
QUnit.test('creme.widgets.actionlist.dependencies (url actions)', function(assert) {
    var delegate = this.createDynamicSelectTag('mock/${ctype}/options', true);
    this.appendOptionTag(delegate, 'a', 1);
    this.appendOptionTag(delegate, 'b', 5);
    this.appendOptionTag(delegate, 'c', 3);

    var element = mock_actionlist_create();
    mock_actionlist_delegate(element, delegate);
    mock_actionlist_add(element, {name: 'create', label: 'create', url: 'mock/create/${rtype}/popup', enabled: true});

    var widget = creme.widget.create(element, {backend: this.backend});
    deepEqual(delegate.creme().widget().dependencies(), ['ctype']);
    deepEqual(widget.dependencies(), ['ctype', 'rtype']);
});
*/

QUnit.test('creme.widgets.actionlist.value', function()
{
    var delegate = this.createDynamicSelectTag(undefined, true);
    this.appendOptionTag(delegate, 'a', 1);
    this.appendOptionTag(delegate, 'b', 5);
    this.appendOptionTag(delegate, 'c', 3);

    var element = mock_actionlist_create();
    mock_actionlist_delegate(element, delegate);
    mock_actionlist_add(element, {name: 'create', label: 'create', url: 'mock/create/popup'});

    var widget = creme.widget.create(element, {backend: this.backend});

    equal(delegate.val(), 1);
    equal(widget.val(), 1);

    widget.val(5);
    equal(delegate.val(), 5);
    equal(widget.val(), 5);

    widget.val(15);
    equal(delegate.val(), 1);
    equal(widget.val(), 1);
});

QUnit.test('creme.widgets.actionlist.reset', function()
{
    var delegate = this.createDynamicSelectTag(undefined, true);
    this.appendOptionTag(delegate, 'a', 12);
    this.appendOptionTag(delegate, 'b', 5);
    this.appendOptionTag(delegate, 'c', 3);

    var element = mock_actionlist_create();
    mock_actionlist_delegate(element, delegate);
    mock_actionlist_add(element, {name: 'create', label: 'create', url: 'mock/create/popup'});

    var widget = creme.widget.create(element, {backend: this.backend});
    widget.val(5);
    equal(delegate.val(), 5);
    equal(widget.val(), 5);

    widget.reset();

    equal(delegate.val(), 12);
    equal(widget.val(), 12);
});

QUnit.test('creme.widgets.actionlist.reload', function(assert) {
    var delegate = this.createDynamicSelectTag(undefined, true);
    this.appendOptionTag(delegate, 'a', 1);
    this.appendOptionTag(delegate, 'b', 5);
    this.appendOptionTag(delegate, 'c', 3);

    var element = mock_actionlist_create();
    mock_actionlist_delegate(element, delegate);
    mock_actionlist_add(element, {name: 'create', label: 'create', url: 'mock/create/popup'});

    var widget = creme.widget.create(element, {backend: this.backend});

    equal(widget.val(), 1);
    deepEqual(widget.dependencies(), []);

    element.creme().widget().url('mock/options');
    this.assertDSelect(delegate, '15', [], 'mock/options', [['15', 'a'], ['5', 'b'], ['3', 'c'], ['14', 't'], ['42', 'y']]);

    equal(widget.val(), 15);
    deepEqual(widget.dependencies(), []);

    element.creme().widget().url('mock/rtype/${ctype}/options')
    element.creme().widget().reload({ctype: 5});

    this.assertDSelect(delegate, 'rtype.7', ['ctype'], 'mock/rtype/5/options', [['rtype.7', 'x'], ['rtype.22', 'y'], ['rtype.3', 'c']]);

    equal(widget.val(), 'rtype.7');
    deepEqual(widget.dependencies(), ['ctype']);
});

QUnit.test('creme.widgets.actionlist.action', function(assert) {
    var delegate = this.createDynamicSelectTag('mock/${ctype}/options', true);
    this.appendOptionTag(delegate, 'a', 1);
    this.appendOptionTag(delegate, 'b', 5);
    this.appendOptionTag(delegate, 'c', 3);

    var element = mock_actionlist_create();
    mock_actionlist_delegate(element, delegate);
    mock_actionlist_add(element, {name: 'create', label: 'create', url: 'mock/create/popup'});
    mock_actionlist_add(element, {name: 'delete', label: 'delete', url: 'mock/delete/popup', disabled:''});
    mock_actionlist_add(element, {name: 'reset', action:'reset', label: 'reset'});

    var widget = creme.widget.create(element, {backend: this.backend});
    deepEqual(widget.dependencies(), ['ctype']);

    equal(widget.actions().length, 3, 'action count');
    assertAction(widget.action('create'), 'create', 'create', undefined, 'mock/create/popup', true);
    assertAction(widget.action('delete'), 'delete', 'delete', undefined, 'mock/delete/popup', false);
    assertAction(widget.action('reset'), 'reset', 'reset', 'reset', undefined, true);
});

}(jQuery));
