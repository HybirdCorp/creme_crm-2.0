QUnit.module("creme.model.renderer.js", {
    setup: function() {
    },

    teardown: function() {
    }
});

assertItems = function(element, expected) {
    var items = $('li', element);

    equal(items.length, expected.length);

    items.each(function(index) {
        equal($(this).html(), expected[index]);
    });
}

QUnit.test('creme.model.ListRenderer.constructor', function(assert) {
    var model = new creme.model.Array();
    var element = $('<ul></ul>');
    var renderer = new creme.model.ListRenderer(element, model);

    equal(model, renderer.model());
    equal(element, renderer.target());

    var renderer = new creme.model.ListRenderer();

    equal(undefined, renderer.model());
    equal(undefined, renderer.target());
});

QUnit.test('creme.model.ListRenderer (empty model)', function(assert) {
    var model = new creme.model.Array();
    var element = $('<ul></ul>');
    var renderer = new creme.model.ListRenderer(element, model);

    equal($('li', element).length, 0);
});

QUnit.test('creme.model.ListRenderer (filled model)', function(assert) {
    var model = new creme.model.Array(['a', 'b']);
    var element = $('<ul></ul>');
    var renderer = new creme.model.ListRenderer(element, model);

    assertItems(element, []);

    renderer.redraw();
    assertItems(element, ['a', 'b']);
});

QUnit.test('creme.model.ListRenderer (empty model, add)', function(assert) {
    var model = new creme.model.Array();
    var element = $('<ul></ul>');
    var renderer = new creme.model.ListRenderer(element, model).redraw();

    assertItems(element, []);

    model.append(['a', 'b']);
    assertItems(element, ['a', 'b']);
});

QUnit.test('creme.model.ListRenderer (filled, model, add)', function(assert) {
    var model = new creme.model.Array(['a', 'b']);
    var element = $('<ul></ul>');
    var renderer = new creme.model.ListRenderer(element, model).redraw();

    assertItems(element, ['a', 'b']);

    model.append(['c', 'd']);
    assertItems(element, ['a', 'b', 'c', 'd']);
});

QUnit.test('creme.model.ListRenderer (remove)', function(assert) {
    var model = new creme.model.Array(['a', 'b', 'c', 'd']);
    var element = $('<ul></ul>');
    var renderer = new creme.model.ListRenderer(element, model).redraw();

    assertItems(element, ['a', 'b', 'c', 'd']);

    model.removeAt(1);
    assertItems(element, ['a', 'c', 'd']);

    model.removeAt(2);
    assertItems(element, ['a', 'c']);
});

QUnit.test('creme.model.ListRenderer (update)', function(assert) {
    var model = new creme.model.Array(['a', 'b', 'c', 'd']);
    var element = $('<ul></ul>');
    var renderer = new creme.model.ListRenderer(element, model).redraw();

    assertItems(element, ['a', 'b', 'c', 'd']);

    model.set('g', 1);
    assertItems(element, ['a', 'g', 'c', 'd']);

    model.set('k', 2);
    assertItems(element, ['a', 'g', 'k', 'd']);
});

QUnit.test('creme.model.ListRenderer (switch model)', function(assert) {
    var model = new creme.model.Array();
    var element = $('<ul></ul>');
    var renderer = new creme.model.ListRenderer(element, model).redraw();

    equal($('option', element).length, 0);

    model.append(['a', 'b']);
    assertItems(element, ['a', 'b']);

    var model = new creme.model.Array(['x', 'y', 'z'])

    renderer.model(model).redraw();
    assertItems(element, ['x', 'y', 'z']);
});

QUnit.test('creme.model.ListRenderer (reset model)', function(assert) {
    var model = new creme.model.Array(['a', 'b', 'c', 'd']);
    var element = $('<ul></ul>');
    var renderer = new creme.model.ListRenderer(element, model).redraw();

    assertItems(element, ['a', 'b', 'c', 'd']);

    model.reset(['g', 'k']);
    assertItems(element, ['g', 'k']);

    model.reset(['x', 'y', 'z', 'a']);
    assertItems(element, ['x', 'y', 'z', 'a']);
});

assertOptions = function(element, expected) {
    var options = $('option', element);

    equal(options.length, expected.length, 'option count');

    options.each(function(index) {
        equal($(this).attr('value'), expected[index].value, 'option %d value'.format(index));
        equal($(this).html(), expected[index].label, 'option %d label'.format(index));

        if (expected.group) {
            equal($(this).parent().is('optgroup'), true, 'option %d has group'.format(index));
            equal($(this).parent().attr('label'), expected.group, 'option %d group label'.format(index));
        }
    });
}

QUnit.test('creme.model.ChoiceRenderer.constructor', function(assert) {
    var model = new creme.model.Array();
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceRenderer(element, model).redraw();

    equal(model, renderer.model());
    equal(element, renderer.target());

    var renderer = new creme.model.ChoiceRenderer();

    equal(undefined, renderer.model());
    equal(undefined, renderer.target());
});

QUnit.test('creme.model.ChoiceRenderer (empty model)', function(assert) {
    var model = new creme.model.Array();
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceRenderer(element, model).redraw();

    equal($('option', element).length, 0);
});

QUnit.test('creme.model.ChoiceRenderer (filled model)', function(assert) {
    var model = new creme.model.Array([{value:1, label:'a'},
                                       {value:2, label:'b'}]);
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceRenderer(element, model).redraw();

    assertOptions(element, [{value:1, label:'a'},
                            {value:2, label:'b'}]);
});

QUnit.test('creme.model.ChoiceRenderer (empty model, add)', function(assert) {
    var model = new creme.model.Array();
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceRenderer(element, model).redraw();

    assertOptions(element, []);

    model.append([{value:1, label:'a'},
                  {value:2, label:'b'}]);

    assertOptions(element, [{value:1, label:'a'},
                            {value:2, label:'b'}]);
});

QUnit.test('creme.model.ChoiceRenderer (empty model, add object)', function(assert) {
    var model = new creme.model.Array();
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceRenderer(element, model).redraw();

    assertOptions(element, []);

    model.append([{value:{id:1, name:'a'}, label:'a'},
                  {value:{id:2, name:'b'}, label:'b'}]);

    assertOptions(element, [{value:$.toJSON({id:1, name:'a'}), label:'a'},
                            {value:$.toJSON({id:2, name:'b'}), label:'b'}]);
});

QUnit.test('creme.model.ChoiceRenderer (filled, model, add)', function(assert) {
    var model = new creme.model.Array([{value:1, label:'a'},
                                       {value:2, label:'b'}]);
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceRenderer(element, model).redraw();

    assertOptions(element, [{value:1, label:'a'},
                            {value:2, label:'b'}]);

    model.append([{value:3, label:'c'},
                  {value:4, label:'d'}]);

    assertOptions(element, [{value:1, label:'a'},
                            {value:2, label:'b'},
                            {value:3, label:'c'},
                            {value:4, label:'d'}]);
});

QUnit.test('creme.model.ChoiceRenderer (filled, model, insert)', function(assert) {
    var model = new creme.model.Array([{value:1, label:'a'},
                                       {value:2, label:'b'},
                                       {value:3, label:'c'}]);
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceRenderer(element, model).redraw();

    assertOptions(element, [{value:1, label:'a'},
                            {value:2, label:'b'},
                            {value:3, label:'c'}]);

    model.insert([{value:8, label:'x'},
                  {value:9, label:'y'}], 1);

    assertOptions(element, [{value:1, label:'a'},
                            {value:8, label:'x'},
                            {value:9, label:'y'},
                            {value:2, label:'b'},
                            {value:3, label:'c'}]);
});

QUnit.test('creme.model.ChoiceRenderer (remove)', function(assert) {
    var model = new creme.model.Array([{value:1, label:'a'},
                                       {value:2, label:'b'},
                                       {value:3, label:'c'},
                                       {value:4, label:'d'}]);
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceRenderer(element, model).redraw();

    assertOptions(element, [{value:1, label:'a'},
                            {value:2, label:'b'},
                            {value:3, label:'c'},
                            {value:4, label:'d'}]);

    model.removeAt(1);

    assertOptions(element, [{value:1, label:'a'},
                            {value:3, label:'c'},
                            {value:4, label:'d'}]);

    model.removeAt(2);

    assertOptions(element, [{value:1, label:'a'},
                            {value:3, label:'c'}]);
});

QUnit.test('creme.model.ChoiceRenderer (update)', function(assert) {
    var model = new creme.model.Array([{value:1, label:'a'},
                                       {value:2, label:'b'},
                                       {value:3, label:'c'},
                                       {value:4, label:'d'}]);
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceRenderer(element, model).redraw();

    assertOptions(element, [{value:1, label:'a'},
                            {value:2, label:'b'},
                            {value:3, label:'c'},
                            {value:4, label:'d'}]);

    model.set({value:58, label:'g'}, 1);

    assertOptions(element, [{value:1, label:'a'},
                            {value:58, label:'g'},
                            {value:3, label:'c'},
                            {value:4, label:'d'}]);

    model.set({value:12, label:'k'}, 2);

    assertOptions(element, [{value:1, label:'a'},
                            {value:58, label:'g'},
                            {value:12, label:'k'},
                            {value:4, label:'d'}]);
});

QUnit.test('creme.model.ChoiceRenderer (switch model)', function(assert) {
    var model = new creme.model.Array();
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceRenderer(element, model).redraw();

    equal($('option', element).length, 0);

    model.append([{value:1, label:'a'},
                  {value:2, label:'b'}]);

    assertOptions(element, [{value:1, label:'a'},
                            {value:2, label:'b'}]);

    var model = new creme.model.Array([{value:8, label:'x'},
                                       {value:7, label:'y'},
                                       {value:6, label:'z'}])

    renderer.model(model).redraw();

    assertOptions(element, [{value:8, label:'x'},
                            {value:7, label:'y'},
                            {value:6, label:'z'}]);
});

QUnit.test('creme.model.ChoiceRenderer (reset model)', function(assert) {
    var model = new creme.model.Array([{value:1, label:'a'},
                                       {value:2, label:'b'},
                                       {value:3, label:'c'},
                                       {value:4, label:'d'}]);
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceRenderer(element, model).redraw();

    assertOptions(element, [{value:1, label:'a'},
                            {value:2, label:'b'},
                            {value:3, label:'c'},
                            {value:4, label:'d'}]);

    model.reset([{value:58, label:'g'},
                 {value:12, label:'k'}]);

    assertOptions(element, [{value:58, label:'g'},
                            {value:12, label:'k'}]);

    model.reset([{value:1, label:'x'},
                 {value:2, label:'y'},
                 {value:3, label:'z'},
                 {value:4, label:'a'}]);

    assertOptions(element, [{value:1, label:'x'},
                            {value:2, label:'y'},
                            {value:3, label:'z'},
                            {value:4, label:'a'}]);
});

QUnit.test('creme.model.ChoiceRenderer (parse)', function(assert) {
    deepEqual([], creme.model.ChoiceRenderer.parse($('<select></select>')));
    deepEqual([], creme.model.ChoiceRenderer.parse($('<select><options></options></select>')));

    deepEqual([{value:'1', label:'a', help: undefined, disabled:false, selected: false, visible: true, tags: []},
               {value:'2', label:'b', help: 'B', disabled:false, selected: true, visible: true, tags: ['tag1']},
               {value:'3', label:'c', help: undefined, disabled:true, selected: false, visible: true, tags: ['tag2']}],
              creme.model.ChoiceRenderer.parse($('<select><options>' +
                                                     '<option value="1">a</option>' +
                                                     '<option value="2" help="B" tags="tag1" selected>b</option>' +
                                                     '<option value="3" tags="tag2" disabled>c</option>' +
                                                 '</options></select>')));
});

QUnit.test('creme.model.ChoiceRenderer.parse (no converter)', function(assert) {
    var element = $('<select><options>' +
                        '<option value="[1, 2]" help="A">a</option>' +
                        '<option value="[3, 4]">b</option>' +
                        '<option value="[5, 6]" help="C">c</option>' +
                    '</options></select>');
    var options = creme.model.ChoiceRenderer.parse(element);

    deepEqual(options, [{value:'[1, 2]', label:'a', help: 'A', disabled:false, selected:true,  visible: true, tags:[]},
                        {value:'[3, 4]', label:'b', help: undefined, disabled:false, selected:false, visible: true, tags:[]},
                        {value:'[5, 6]', label:'c', help: 'C', disabled:false, selected:false, visible: true, tags:[]},]);

    element = $('<select><options>' +
                    '<option value="[1, 2]">a</option>' +
                    '<option value="[3, 4]" help="B" selected>b</option>' +
                    '<option value="[5, 6]" disabled>c</option>' +
                '</options></select>');
    options = creme.model.ChoiceRenderer.parse(element);

    deepEqual(options, [{value:'[1, 2]', label:'a', help: undefined, disabled:false, selected:false, visible: true, tags:[]},
                        {value:'[3, 4]', label:'b', help: 'B', disabled:false, selected:true,  visible: true, tags:[]},
                        {value:'[5, 6]', label:'c', help: undefined, disabled:true,  selected:false, visible: true, tags:[]},]);

    element.val("[1, 2]");
    options = creme.model.ChoiceRenderer.parse(element);

    deepEqual(options, [{value:'[1, 2]', label:'a', help: undefined, disabled:false, selected:true,  visible: true, tags:[]},
                        {value:'[3, 4]', label:'b', help: 'B', disabled:false, selected:false, visible: true, tags:[]},
                        {value:'[5, 6]', label:'c', help: undefined, disabled:true,  selected:false, visible: true, tags:[]},]);
});

QUnit.test('creme.model.ChoiceRenderer.parse (converter)', function(assert) {
    var element = $('<select><options>' +
            '<option value="[1, 2]">a</option>' +
            '<option value="[3, 4]">b</option>' +
            '<option value="[5, 6]">c</option>' +
        '</options></select>');
    var options = creme.model.ChoiceRenderer.parse(element, new creme.utils.JSON().decode);

    deepEqual(options, [{value:[1, 2], label:'a', help: undefined, disabled:false, selected:true,  visible: true, tags:[]},
                        {value:[3, 4], label:'b', help: undefined, disabled:false, selected:false, visible: true, tags:[]},
                        {value:[5, 6], label:'c', help: undefined, disabled:false, selected:false, visible: true, tags:[]},]);

    element = $('<select><options>' +
                    '<option value="[1, 2]">a</option>' +
                    '<option value="[3, 4]" selected>b</option>' +
                    '<option value="[5, 6]" disabled>c</option>' +
                '</options></select>');
    options = creme.model.ChoiceRenderer.parse(element, new creme.utils.JSON().decode);

    deepEqual(options, [{value:[1, 2], label:'a', help: undefined, disabled:false, selected:false, visible: true, tags:[]},
                        {value:[3, 4], label:'b', help: undefined, disabled:false, selected:true,  visible: true, tags:[]},
                        {value:[5, 6], label:'c', help: undefined, disabled:true, selected:false,  visible: true, tags:[]},]);

    element.val("[1, 2]");
    options = creme.model.ChoiceRenderer.parse(element, new creme.utils.JSON().decode);

    deepEqual(options, [{value:[1, 2], label:'a', help: undefined, disabled:false, selected:true,  visible: true, tags:[]},
                        {value:[3, 4], label:'b', help: undefined, disabled:false, selected:false, visible: true, tags:[]},
                        {value:[5, 6], label:'c', help: undefined, disabled:true,  selected:false, visible: true, tags:[]},]);
});

QUnit.test('creme.model.ChoiceRenderer.choicesFromTuples ([])', function(assert) {
    var options = creme.model.ChoiceRenderer.choicesFromTuples();
    deepEqual([], options);

    options = creme.model.ChoiceRenderer.choicesFromTuples([]);
    deepEqual([], options);
});

QUnit.test('creme.model.ChoiceRenderer.choicesFromTuples ([value, label])', function(assert) {
    var data = [[[1, 2], 'a'], [[3, 4], 'b'], [[5, 6], 'c']];
    var options = creme.model.ChoiceRenderer.choicesFromTuples(data);

    deepEqual(options, [{value:[1, 2], label:'a', help: undefined, disabled:false, selected:false, visible: true},
                        {value:[3, 4], label:'b', help: undefined, disabled:false, selected:false, visible: true},
                        {value:[5, 6], label:'c', help: undefined, disabled:false, selected:false, visible: true}]);
});

QUnit.test('creme.model.ChoiceRenderer.choicesFromTuples (value)', function(assert) {
    var data = ['a', 'b', 'c', null];
    var options = creme.model.ChoiceRenderer.choicesFromTuples(data);

    deepEqual(options, [{value:'a', label:'a', help: undefined, disabled:false, selected:false, visible: true},
                        {value:'b', label:'b', help: undefined, disabled:false, selected:false, visible: true},
                        {value:'c', label:'c', help: undefined, disabled:false, selected:false, visible: true},
                        {value:null, label:'null', help: undefined, disabled:false, selected:false, visible: true}]);
});

QUnit.test('creme.model.ChoiceRenderer.choicesFromTuples ({value: value, label:label})', function(assert) {
    var data = [{value:[1, 2], label:'a'},
                {value:[3, 4], label:'b'},
                {value:[5, 6], label:'c'},
                {value:7},
                {value:null, label:'empty'}];
    var options = creme.model.ChoiceRenderer.choicesFromTuples(data);

    deepEqual(options, [{value:[1, 2], label:'a', help: undefined, disabled:false, selected:false, visible: true},
                        {value:[3, 4], label:'b', help: undefined, disabled:false, selected:false, visible: true},
                        {value:[5, 6], label:'c', help: undefined, disabled:false, selected:false, visible: true},
                        {value:7, label:'7', help: undefined, disabled:false, selected:false, visible: true},
                        {value:null, label:'empty', help: undefined, disabled:false, selected:false, visible: true}]);
});

assertOptionGroups = function(element, expected) {
    var groups = $('optgroup', element);

    equal(groups.length, expected.length, 'optgroup count');

    groups.each(function(index) {
        equal($(this).attr('label'), expected[index], 'optgroup %d'.format(index));
    });
}

QUnit.test('creme.model.ChoiceGroupRenderer (empty model, add)', function(assert) {
    var model = new creme.model.Array();
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceGroupRenderer(element, model).redraw();

    assertOptionGroups(element, []);
    assertOptions(element, []);

    model.append([{value:1, label:'a'},
                  {value:2, label:'b'},
                  {group: 'group1', value:3, label:'c'},
                  {group: 'group1', value:4, label:'d'},
                  {group: 'group2', value:5, label:'e'}]);

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {value:2, label:'b'},
                            {group: 'group1', value:3, label:'c'},
                            {group: 'group1', value:4, label:'d'},
                            {group: 'group2', value:5, label:'e'}]);
});
QUnit.test('creme.model.ChoiceGroupRenderer (filled model)', function(assert) {
    var model = new creme.model.Array([{value:1, label:'a'},
                                       {value:2, label:'b'},
                                       {group: 'group1', value:3, label:'c'},
                                       {group: 'group1', value:4, label:'d'},
                                       {group: 'group2', value:5, label:'e'}]);
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceGroupRenderer(element, model).redraw();

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {value:2, label:'b'},
                            {group: 'group1', value:3, label:'c'},
                            {group: 'group1', value:4, label:'d'},
                            {group: 'group2', value:5, label:'e'}]);
});


QUnit.test('creme.model.ChoiceGroupRenderer (filled, model, add)', function(assert) {
    var model = new creme.model.Array([{value:1, label:'a'},
                                       {value:2, label:'b'}]);
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceGroupRenderer(element, model).redraw();

    assertOptionGroups(element, []);
    assertOptions(element, [{value:1, label:'a'},
                            {value:2, label:'b'}]);

    model.append([{group: 'group1', value:3, label:'c'},
                  {group: 'group1', value:4, label:'d'}]);

    assertOptionGroups(element, ['group1']);
    assertOptions(element, [{value:1, label:'a'},
                            {value:2, label:'b'},
                            {group: 'group1', value:3, label:'c'},
                            {group: 'group1', value:4, label:'d'}]);
});

QUnit.test('creme.model.ChoiceGroupRenderer (filled, model, add, same group)', function(assert) {
    var model = new creme.model.Array([{value:1, label:'a'},
                                       {group: 'group1', value:2, label:'b'},
                                       {group: 'group2', value:3, label:'c'}]);
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceGroupRenderer(element, model).redraw();

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group: 'group1', value:2, label:'b'},
                            {group: 'group2', value:3, label:'c'}]);

    model.append([{group: 'group1', value:8, label:'x'},
                  {group: 'group1', value:9, label:'y'}]);

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group: 'group1', value:2, label:'b'},
                            {group: 'group1', value:8, label:'x'},
                            {group: 'group1', value:9, label:'y'},
                            {group: 'group2', value:3, label:'c'}]);

    model.append([{group: 'group2', value:10, label:'z'}]);

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group: 'group1', value:2, label:'b'},
                            {group: 'group1', value:8, label:'x'},
                            {group: 'group1', value:9, label:'y'},
                            {group: 'group2', value:3, label:'c'},
                            {group: 'group2', value:10, label:'z'}]);
});

QUnit.test('creme.model.ChoiceGroupRenderer (filled, model, insert, same group)', function(assert) {
    var model = new creme.model.Array([{value:1, label:'a'},
                                       {group:'group1', value:2, label:'b'},
                                       {group:'group2', value:3, label:'c'}]);
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceGroupRenderer(element, model).redraw();

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:2, label:'b'},
                            {group:'group2', value:3, label:'c'}]);

    model.insert([{group:'group1', value:8, label:'x'},
                  {group:'group1', value:9, label:'y'}], 1);

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:8, label:'x'},
                            {group:'group1', value:9, label:'y'},
                            {group:'group1', value:2, label:'b'},
                            {group:'group2', value:3, label:'c'}]);
});

QUnit.test('creme.model.ChoiceGroupRenderer (filled, model, insert, other group)', function(assert) {
    var model = new creme.model.Array([{value:1, label:'a'},
                                       {group:'group1', value:2, label:'b'},
                                       {group:'group2', value:3, label:'c'}]);
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceGroupRenderer(element, model).redraw();

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:2, label:'b'},
                            {group:'group2', value:3, label:'c'}]);

    model.insert([{group:'group1', value:8, label:'x'},
                  {group:'group1', value:9, label:'y'}], 1);

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:8, label:'x'},
                            {group:'group1', value:9, label:'y'},
                            {group:'group1', value:2, label:'b'},
                            {group:'group2', value:3, label:'c'}]);
});

QUnit.test('creme.model.ChoiceGroupRenderer (filled, model, remove)', function(assert) {
    var model = new creme.model.Array([{value:1, label:'a'},
                                       {value:2, label:'b'},
                                       {group:'group2', value:3, label:'c'}]);
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceGroupRenderer(element, model).redraw();

    assertOptionGroups(element, ['group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {value:2, label:'b'},
                            {group:'group2', value:3, label:'c'}]);

    model.removeAt(1);

    assertOptionGroups(element, ['group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group2', value:3, label:'c'}]);

    model.removeAt(0);

    assertOptionGroups(element, ['group2']);
    assertOptions(element, [{group:'group2', value:3, label:'c'}]);
});

QUnit.test('creme.model.ChoiceGroupRenderer (filled, model, remove, empty group)', function(assert) {
    var model = new creme.model.Array([{value:1, label:'a'},
                                       {group:'group1', value:2, label:'b'},
                                       {group:'group2', value:3, label:'c'}]);
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceGroupRenderer(element, model).redraw();

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:2, label:'b'},
                            {group:'group2', value:3, label:'c'}]);

    model.removeAt(1);

    assertOptionGroups(element, ['group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group2', value:3, label:'c'}]);

    model.removeAt(1);

    assertOptionGroups(element, []);
    assertOptions(element, [{value:1, label:'a'}]);
});

QUnit.test('creme.model.ChoiceGroupRenderer (filled, model, remove, group)', function(assert) {
    var model = new creme.model.Array([{value:1, label:'a'},
                                       {group:'group1', value:2, label:'b'},
                                       {group:'group1', value:2.5, label:'b.5'},
                                       {group:'group2', value:3, label:'c'},
                                       {group:'group2', value:4, label:'d'}]);
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceGroupRenderer(element, model).redraw();

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:2, label:'b'},
                            {group:'group1', value:2.5, label:'b.5'},
                            {group:'group2', value:3, label:'c'},
                            {group:'group2', value:4, label:'d'}]);

    model.removeAt(1);

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:2.5, label:'b.5'},
                            {group:'group2', value:3, label:'c'},
                            {group:'group2', value:4, label:'d'}]);

    model.removeAt(2);

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:2.5, label:'b.5'},
                            {group:'group2', value:4, label:'d'}]);

    model.removeAt(2);

    assertOptionGroups(element, ['group1']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:2.5, label:'b.5'}]);
});

QUnit.test('creme.model.ChoiceGroupRenderer (filled, model, update, same group)', function(assert) {
    var model = new creme.model.Array([{value:1, label:'a'},
                                       {group:'group1', value:2, label:'b'},
                                       {group:'group1', value:2.5, label:'b.5'},
                                       {group:'group2', value:3, label:'c'},
                                       {group:'group2', value:4, label:'d'}]);
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceGroupRenderer(element, model).redraw();

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:2, label:'b'},
                            {group:'group1', value:2.5, label:'b.5'},
                            {group:'group2', value:3, label:'c'},
                            {group:'group2', value:4, label:'d'}]);

    model.set({group:'group1', value:57, label:'b.57'}, 2);

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:2, label:'b'},
                            {group:'group1', value:57, label:'b.57'},
                            {group:'group2', value:3, label:'c'},
                            {group:'group2', value:4, label:'d'}]);
});

QUnit.test('creme.model.ChoiceGroupRenderer (filled, model, update, other group)', function(assert) {
    var model = new creme.model.Array([{value:1, label:'a'},
                                       {group:'group1', value:2, label:'b'},
                                       {group:'group1', value:2.5, label:'b.5'},
                                       {group:'group2', value:3, label:'c'},
                                       {group:'group2', value:4, label:'d'}]);
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceGroupRenderer(element, model).redraw();

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:2, label:'b'},
                            {group:'group1', value:2.5, label:'b.5'},
                            {group:'group2', value:3, label:'c'},
                            {group:'group2', value:4, label:'d'}]);

    model.set({group:'group2', value:57, label:'b.57'}, 2);

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:2, label:'b'},
                            {group:'group2', value:3, label:'c'},
                            {group:'group2', value:4, label:'d'},
                            {group:'group2', value:57, label:'b.57'}]);

    model.set({group:'group1', value:4, label:'d'}, 3);

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:2, label:'b'},
                            {group:'group1', value:4, label:'d'},
                            {group:'group2', value:3, label:'c'},
                            {group:'group2', value:57, label:'b.57'}]);

    model.set({group:'group2', value:4, label:'d'}, 2);

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:2, label:'b'},
                            {group:'group2', value:4, label:'d'},
                            {group:'group2', value:3, label:'c'},
                            {group:'group2', value:57, label:'b.57'}]);
});

QUnit.test('creme.model.ChoiceGroupRenderer (filled, model, update, create group)', function(assert) {
    var model = new creme.model.Array([{value:1, label:'a'},
                                       {group:'group1', value:2, label:'b'},
                                       {group:'group1', value:3, label:'c'},
                                       {group:'group2', value:4, label:'d'}]);
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceGroupRenderer(element, model).redraw();

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:2, label:'b'},
                            {group:'group1', value:3, label:'c'},
                            {group:'group2', value:4, label:'d'}]);

    model.set({group:'group3', value:57, label:'c'}, 2);

    assertOptionGroups(element, ['group1', 'group2', 'group3']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:2, label:'b'},
                            {group:'group2', value:4, label:'d'},
                            {group:'group3', value:57, label:'c'}]);
});

QUnit.test('creme.model.ChoiceGroupRenderer (filled, model, update, remove group)', function(assert) {
    var model = new creme.model.Array([{value:1, label:'a'},
                                       {group:'group1', value:2, label:'b'},
                                       {group:'group1', value:3, label:'c'},
                                       {group:'group2', value:4, label:'d'}]);
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceGroupRenderer(element, model).redraw();

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:2, label:'b'},
                            {group:'group1', value:3, label:'c'},
                            {group:'group2', value:4, label:'d'}]);

    model.set({value:57, label:'c'}, 2);

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:2, label:'b'},
                            {group:'group2', value:4, label:'d'},
                            {value:57, label:'c'}]);
});

QUnit.test('creme.model.ChoiceGroupRenderer (filled, model, update, other group, empty)', function(assert) {
    var model = new creme.model.Array([{value:1, label:'a'},
                                       {group:'group1', value:2, label:'b'},
                                       {group:'group2', value:3, label:'c'},
                                       {group:'group2', value:4, label:'d'}]);
    var element = $('<select><options></options></select>');
    var renderer = new creme.model.ChoiceGroupRenderer(element, model).redraw();

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:2, label:'b'},
                            {group:'group2', value:3, label:'c'},
                            {group:'group2', value:4, label:'d'}]);

    model.set({group:'group2', value:57, label:'b.57'}, 1);

    assertOptionGroups(element, ['group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group2', value:3, label:'c'},
                            {group:'group2', value:4, label:'d'},
                            {group:'group2', value:57, label:'b.57'}]);

    model.set({group:'group1', value:4, label:'d'}, 2);

    assertOptionGroups(element, ['group1', 'group2']);
    assertOptions(element, [{value:1, label:'a'},
                            {group:'group1', value:4, label:'d'},
                            {group:'group2', value:3, label:'c'},
                            {group:'group2', value:57, label:'b.57'}]);
});

QUnit.test('creme.model.ChoiceGroupRenderer (parse)', function(assert) {
    deepEqual([{group: undefined, value:'1', label:'a', help: undefined, disabled:false, selected: false, visible: true, tags: []},
               {group: 'group1',  value:'2', label:'b', help: undefined, disabled:false, selected: true,  visible: true, tags: ['tag1']},
               {group: 'group2',  value:'3', label:'c', help: undefined, disabled:true,  selected: false, visible: true, tags: ['tag2']},
               {group: 'group2',  value:'4', label:'d', help: undefined, disabled:false, selected: false, visible: true, tags: []},
               {group: undefined, value:'5', label:'e', help: undefined, disabled:false, selected: false, visible: true, tags: []},
               {group: undefined, value:'6', label:'f', help: undefined, disabled:false, selected: false, visible: true, tags: []}],
              creme.model.ChoiceGroupRenderer.parse($('<select><options>' +
                                                     '<option value="1">a</option>' +
                                                     '<optgroup label="group1">' +
                                                         '<option value="2" tags="tag1" selected>b</option>' +
                                                     '</optgroup>' +
                                                     '<optgroup label="group2">' +
                                                         '<option value="3" tags="tag2" disabled>c</option>' +
                                                         '<option value="4">d</option>' +
                                                     '</optgroup>' +
                                                     '<option value="5">e</option>' +
                                                     '<option value="6">f</option>' +
                                                 '</options></select>')));
});

QUnit.test('creme.model.ChoiceGroupRenderer.choicesFromTuples ([])', function(assert) {
    var options = creme.model.ChoiceGroupRenderer.choicesFromTuples();
    deepEqual([], options);

    options = creme.model.ChoiceGroupRenderer.choicesFromTuples([]);
    deepEqual([], options);
});

QUnit.test('creme.model.ChoiceGroupRenderer.choicesFromTuples ([value, label])', function(assert) {
    var data = [[1, 'a'], [24, 'b'], [5, 'D'], [12.5, 'c']];
    var options = creme.model.ChoiceGroupRenderer.choicesFromTuples(data);

    deepEqual(options, [{group: undefined, value:1,    label:'a', help: undefined, disabled:false, selected:false, visible: true},
                        {group: undefined, value:24,   label:'b', help: undefined, disabled:false, selected:false, visible: true},
                        {group: undefined, value:5,    label:'D', help: undefined, disabled:false, selected:false, visible: true},
                        {group: undefined, value:12.5, label:'c', help: undefined, disabled:false, selected:false, visible: true}]);
});

QUnit.test('creme.model.ChoiceGroupRenderer.choicesFromTuples ([value, label, group])', function(assert) {
    var data = [[[1, 2], 'a'], [[3, 4], 'b', 'group1'], [[5, 6], 'c', 'group2'], [7, 'd', 'group1']];
    var options = creme.model.ChoiceGroupRenderer.choicesFromTuples(data);

    deepEqual(options, [{group: undefined, value:[1, 2], label:'a', help: undefined, disabled:false, selected:false, visible: true},
                        {group: 'group1',  value:[3, 4], label:'b', help: undefined, disabled:false, selected:false, visible: true},
                        {group: 'group2',  value:[5, 6], label:'c', help: undefined, disabled:false, selected:false, visible: true},
                        {group: 'group1',  value:7,      label:'d', help: undefined, disabled:false, selected:false, visible: true}]);
});

QUnit.test('creme.model.ChoiceGroupRenderer.choicesFromTuples (value)', function(assert) {
    var data = ['a', 'b', 'c', null];
    var options = creme.model.ChoiceGroupRenderer.choicesFromTuples(data);

    deepEqual(options, [{group: undefined, value:'a', label:'a', help: undefined, disabled:false, selected:false, visible: true},
                        {group: undefined, value:'b', label:'b', help: undefined, disabled:false, selected:false, visible: true},
                        {group: undefined, value:'c', label:'c', help: undefined, disabled:false, selected:false, visible: true},
                        {group: undefined, value:null, label:'null', help: undefined, disabled:false, selected:false, visible: true}]);
});

QUnit.test('creme.model.ChoiceGroupRenderer.choicesFromTuples ({value: value, label:label})', function(assert) {
    var data = [{value:[1, 2], label:'a'},
                {value:[3, 4], label:'b', group:'group1'},
                {value:[5, 6], label:'c', group:'group2'},
                {value:7, label:'d', group:'group1'},
                {value:8, group:'group2'},
                {value:null, group:'group2'},
                {value:null, label:'empty', group:'group2'}];

    var options = creme.model.ChoiceGroupRenderer.choicesFromTuples(data);

    deepEqual(options, [{group: undefined, value:[1, 2], label:'a',     help: undefined, disabled:false, selected:false, visible: true},
                        {group: 'group1',  value:[3, 4], label:'b',     help: undefined, disabled:false, selected:false, visible: true},
                        {group: 'group2',  value:[5, 6], label:'c',     help: undefined, disabled:false, selected:false, visible: true},
                        {group: 'group1',  value:7,      label:'d',     help: undefined, disabled:false, selected:false, visible: true},
                        {group: 'group2',  value:8,      label:'8',     help: undefined, disabled:false, selected:false, visible: true},
                        {group: 'group2',  value:null,   label:'null',  help: undefined, disabled:false, selected:false, visible: true},
                        {group: 'group2',  value:null,   label:'empty', help: undefined, disabled:false, selected:false, visible: true}]);
});
