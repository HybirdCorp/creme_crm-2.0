QUnit.module("creme.component.EventHandler.js", {
  setup: function() {
      this.resetMockCalls();
  },

  teardown: function() {},

  resetMockCalls: function() {
      this._eventListenerCalls = [];
  },

  mockListener: function(name) {
      var self = this;
      return (function(name) {return function() {
          self._eventListenerCalls.push([name, this].concat(Array.copy(arguments)));
      }})(name);
  },

  assertRaises: function(block, expected, message) {
      QUnit.assert.raises(block,
             function(error) {
                  ok(error instanceof expected, 'error is ' + expected);
                  equal(message, '' + error);
                  return true;
             });
  }
});

function assertListenerUUIDs(listeners, expected) {
    var uuid_getter = function(l) {return l.__eventuuid__;};
    deepEqual(listeners.map(uuid_getter), expected.map(uuid_getter));
}

QUnit.test('creme.component.EventHandler.bind (single key, single listener)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1'),
        listener2 = this.mockListener('2');

    deepEqual({}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));

    handler.bind('event1', listener);

    deepEqual({'event1':[listener]}, handler._listeners);
    deepEqual([listener], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));

    handler.bind('event2', listener);

    deepEqual({'event1':[listener], 'event2':[listener]}, handler._listeners);
    deepEqual([listener], handler.listeners('event1'));
    deepEqual([listener], handler.listeners('event2'));

    handler.bind('event1', listener2);

    deepEqual({'event1':[listener, listener2], 'event2':[listener]}, handler._listeners);
    deepEqual([listener, listener2], handler.listeners('event1'));
    deepEqual([listener], handler.listeners('event2'));

    handler.trigger('event1', 'a');
    deepEqual([['1', handler, 'event1', 'a'], ['2', handler, 'event1', 'a']], this._eventListenerCalls);

    this.resetMockCalls();

    handler.trigger('event2', 'b');
    deepEqual([['1', handler, 'event2', 'b']], this._eventListenerCalls);
});

QUnit.test('creme.component.EventHandler.bind (single key, multiple listener)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1'),
        listener2 = this.mockListener('2');

    deepEqual({}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));

    handler.bind('event1', [listener, listener2]);

    deepEqual({'event1':[listener, listener2]}, handler._listeners);
    deepEqual([listener, listener2], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));

    handler.trigger('event1', 'a');
    deepEqual([['1', handler, 'event1', 'a'], ['2', handler, 'event1', 'a']], this._eventListenerCalls);
});

QUnit.test('creme.component.EventHandler.bind (multiple key, single listener)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1'),
        listener2 = this.mockListener('2');

    deepEqual({}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));
    deepEqual([], handler.listeners('event3'));

    handler.bind(['event1', 'event2'], listener);

    deepEqual({'event1':[listener], 'event2':[listener]}, handler._listeners);
    deepEqual([listener], handler.listeners('event1'));
    deepEqual([listener], handler.listeners('event2'));
    deepEqual([], handler.listeners('event3'));

    handler.bind(['event1', 'event2', 'event3'], listener2);

    deepEqual({'event1':[listener, listener2], 'event2':[listener, listener2], 'event3':[listener2]}, handler._listeners);
    deepEqual([listener, listener2], handler.listeners('event1'));
    deepEqual([listener, listener2], handler.listeners('event2'));
    deepEqual([listener2], handler.listeners('event3'));

    handler.trigger('event1', 'a');
    deepEqual([['1', handler, 'event1', 'a'], ['2', handler, 'event1', 'a']], this._eventListenerCalls);

    this.resetMockCalls();

    handler.trigger('event2', 'b');
    deepEqual([['1', handler, 'event2', 'b'], ['2', handler, 'event2', 'b']], this._eventListenerCalls);

    this.resetMockCalls();

    handler.trigger('event3', 'd');
    deepEqual([['2', handler, 'event3', 'd']], this._eventListenerCalls);

    handler.trigger('event3', 'd');
    deepEqual([['2', handler, 'event3', 'd'], ['2', handler, 'event3', 'd']], this._eventListenerCalls);
});

QUnit.test('creme.component.EventHandler.bind (multiple key, multiple listener)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1'),
        listener2 = this.mockListener('2');

    deepEqual({}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));
    deepEqual([], handler.listeners('event3'));

    handler.bind(['event1', 'event2'], [listener, listener2]);

    deepEqual({'event1':[listener, listener2], 'event2':[listener, listener2]}, handler._listeners);
    deepEqual([listener, listener2], handler.listeners('event1'));
    deepEqual([listener, listener2], handler.listeners('event2'));
    deepEqual([], handler.listeners('event3'));

    handler.bind(['event1', 'event2', 'event3'], [listener, listener2]);

    deepEqual({'event1':[listener, listener2, listener, listener2], 
               'event2':[listener, listener2, listener, listener2],
               'event3':[listener, listener2]}, handler._listeners);
    deepEqual([listener, listener2, listener, listener2], handler.listeners('event1'));
    deepEqual([listener, listener2, listener, listener2], handler.listeners('event2'));
    deepEqual([listener, listener2], handler.listeners('event3'));
});

QUnit.test('creme.component.EventHandler.bind (split key, multiple listener)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1'),
        listener2 = this.mockListener('2');

    deepEqual({}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));
    deepEqual([], handler.listeners('event3'));

    handler.bind('event1 event2', [listener, listener2]);

    deepEqual({'event1':[listener, listener2], 'event2':[listener, listener2]}, handler._listeners);
    deepEqual([listener, listener2], handler.listeners('event1'));
    deepEqual([listener, listener2], handler.listeners('event2'));
    deepEqual([], handler.listeners('event3'));

    handler.bind('event1 event2 event3', [listener, listener2]);

    deepEqual({'event1':[listener, listener2, listener, listener2], 
               'event2':[listener, listener2, listener, listener2],
               'event3':[listener, listener2]}, handler._listeners);
    deepEqual([listener, listener2, listener, listener2], handler.listeners('event1'));
    deepEqual([listener, listener2, listener, listener2], handler.listeners('event2'));
    deepEqual([listener, listener2], handler.listeners('event3'));
});

QUnit.test('creme.component.EventHandler.bind (decorator)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1'),
        listener2 = this.mockListener('2');
    var decorator = function(key, listener, args) {
        return listener.apply(this, args.concat(['decorated']));
    }

    deepEqual({}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));
    deepEqual([], handler.listeners('event3'));

    handler.bind(['event1', 'event2'], listener);
    handler.bind(['event1', 'event3'], listener2, decorator);

    handler.trigger('event1');
    deepEqual([['1', handler, 'event1'], ['2', handler, 'event1', 'decorated']], this._eventListenerCalls);
    
    this.resetMockCalls();
    handler.trigger('event2', 12);
    deepEqual([['1', handler, 'event2', 12]], this._eventListenerCalls);

    this.resetMockCalls();
    handler.trigger('event3', 38);
    deepEqual([['2', handler, 'event3', 38, 'decorated']], this._eventListenerCalls);
});

QUnit.test('creme.component.EventHandler.bind (object)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listeners = {
            event1: this.mockListener('1'),
            event2: [this.mockListener('2'), this.mockListener('3')]
        }

    deepEqual({}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));

    handler.bind(listeners);

    deepEqual({'event1':[listeners.event1], 
               'event2':[listeners.event2[0], listeners.event2[1]]}, handler._listeners);

    handler.trigger('event1');
    deepEqual([['1', handler, 'event1']], this._eventListenerCalls);

    this.resetMockCalls();
    handler.trigger('event2');
    deepEqual([['2', handler, 'event2'], ['3', handler, 'event2']], this._eventListenerCalls);

    this.resetMockCalls();
    handler.trigger('event3');
    deepEqual([], this._eventListenerCalls);
});

QUnit.test('creme.component.EventHandler.bind (object array)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listeners1 = {
            event1: this.mockListener('1'),
            event2: [this.mockListener('2'), this.mockListener('3')]
        },
        listeners2 = {
            event1: this.mockListener('2.1'),
            event3: [this.mockListener('2.2'), this.mockListener('2.3')]
        };

    deepEqual({}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));
    deepEqual([], handler.listeners('event3'));

    handler.bind([listeners1, listeners2]);

    deepEqual({'event1':[listeners1.event1, listeners2.event1], 
               'event2':[listeners1.event2[0], listeners1.event2[1]],
               'event3':[listeners2.event3[0], listeners2.event3[1]]}, handler._listeners);

    handler.trigger('event1');
    deepEqual([['1', handler, 'event1'], ['2.1', handler, 'event1']], this._eventListenerCalls);

    this.resetMockCalls();
    handler.trigger('event2');
    deepEqual([['2', handler, 'event2'], ['3', handler, 'event2']], this._eventListenerCalls);

    this.resetMockCalls();
    handler.trigger('event3');
    deepEqual([['2.2', handler, 'event3'], ['2.3', handler, 'event3']], this._eventListenerCalls);
});

QUnit.test('creme.component.EventHandler.bind (errors)', function(assert) {
    var handler = new creme.component.EventHandler();

    this.assertRaises(function() {
        handler.bind('event1', 'b');
    }, Error, 'Error: unable to bind event "event1", listener is not a function');

    this.assertRaises(function() {
        handler.on('event1', 'b');
    }, Error, 'Error: unable to bind event "event1", listener is not a function');

    this.assertRaises(function() {
        handler.on({
            'event1': function() {},
            'event2': 'b'
        });
    }, Error, 'Error: unable to bind event "event2", listener is not a function');
});

QUnit.test('creme.component.EventHandler.on/off (bind/unbind aliases)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1');

    handler.on('event1', listener);

    handler.trigger('event1');
    deepEqual([['1', handler, 'event1']], this._eventListenerCalls);

    handler.off('event1', listener);

    this.resetMockCalls();
    handler.trigger('event1');

    deepEqual([], this._eventListenerCalls);
});

QUnit.test('creme.component.EventHandler.trigger', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1'),
        listener2 = this.mockListener('2');

    handler.bind('event1', listener);
    handler.bind(['event1', 'event2'], listener2);

    handler.trigger('event1');
    deepEqual([['1', handler, 'event1'], ['2', handler, 'event1']], this._eventListenerCalls);

    this.resetMockCalls();
    handler.trigger('event1', [], this);
    deepEqual([['1', this, 'event1'], ['2', this, 'event1']], this._eventListenerCalls);

    this.resetMockCalls();
    handler.trigger('event1', ['a', 12], this);
    deepEqual([['1', this, 'event1', 'a', 12], ['2', this, 'event1', 'a', 12]], this._eventListenerCalls);
});

QUnit.test('creme.component.EventHandler.unbind (single key, single listener)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1'),
        listener2 = this.mockListener('2');

    handler.bind('event1', listener);
    handler.bind(['event1', 'event2'], listener2);

    deepEqual({'event1':[listener, listener2], 'event2':[listener2]}, handler._listeners);
    deepEqual([listener, listener2], handler.listeners('event1'));
    deepEqual([listener2], handler.listeners('event2'));

    handler.unbind('event2', listener); // not bound, do nothing

    deepEqual({'event1':[listener, listener2], 'event2':[listener2]}, handler._listeners);
    deepEqual([listener, listener2], handler.listeners('event1'));
    deepEqual([listener2], handler.listeners('event2'));

    handler.unbind('event1', listener);

    deepEqual({'event1':[listener2], 'event2':[listener2]}, handler._listeners);
    deepEqual([listener2], handler.listeners('event1'));
    deepEqual([listener2], handler.listeners('event2'));

    handler.unbind('event1', listener);

    deepEqual({'event1':[listener2], 'event2':[listener2]}, handler._listeners);
    deepEqual([listener2], handler.listeners('event1'));
    deepEqual([listener2], handler.listeners('event2'));
});

QUnit.test('creme.component.EventHandler.unbind (single key, multiple listener)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1'),
        listener2 = this.mockListener('2');

    handler.bind('event1', listener);
    handler.bind(['event1', 'event2'], listener2);

    deepEqual({'event1':[listener, listener2], 'event2':[listener2]}, handler._listeners);
    deepEqual([listener, listener2], handler.listeners('event1'));
    deepEqual([listener2], handler.listeners('event2'));

    handler.unbind('event1', [listener, listener2]);

    deepEqual({'event1':[], 'event2':[listener2]}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([listener2], handler.listeners('event2'));

    handler.unbind('event1', [listener, listener2]);

    deepEqual({'event1':[], 'event2':[listener2]}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([listener2], handler.listeners('event2'));
});

QUnit.test('creme.component.EventHandler.unbind (multiple key, single listener)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1'),
        listener2 = this.mockListener('2');

    handler.bind('event1', listener);
    handler.bind(['event1', 'event2'], listener2);

    deepEqual({'event1':[listener, listener2], 'event2':[listener2]}, handler._listeners);
    deepEqual([listener, listener2], handler.listeners('event1'));
    deepEqual([listener2], handler.listeners('event2'));

    handler.unbind(['event1', 'event2'], [listener2]);

    deepEqual({'event1':[listener], 'event2':[]}, handler._listeners);
    deepEqual([listener], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));

    handler.unbind(['event1', 'event2'], [listener2]);

    deepEqual({'event1':[listener], 'event2':[]}, handler._listeners);
    deepEqual([listener], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));
});

QUnit.test('creme.component.EventHandler.unbind (multiple key, multiple listener)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1'),
        listener2 = this.mockListener('2');

    handler.bind('event1', listener);
    handler.bind(['event1', 'event2'], listener2);

    deepEqual({'event1':[listener, listener2], 'event2':[listener2]}, handler._listeners);
    deepEqual([listener, listener2], handler.listeners('event1'));
    deepEqual([listener2], handler.listeners('event2'));

    handler.unbind(['event1', 'event2'], [listener, listener2]);

    deepEqual({'event1':[], 'event2':[]}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));

    handler.unbind(['event1', 'event2'], [listener, listener2]);

    deepEqual({'event1':[], 'event2':[]}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));
});

QUnit.test('creme.component.EventHandler.unbind (single key, all listeners)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1'),
        listener2 = this.mockListener('2');

    handler.bind('event1', listener);
    handler.bind(['event1', 'event2'], listener2);

    deepEqual({'event1':[listener, listener2], 'event2':[listener2]}, handler._listeners);
    deepEqual([listener, listener2], handler.listeners('event1'));
    deepEqual([listener2], handler.listeners('event2'));

    handler.unbind('event1');

    deepEqual({'event1':[], 'event2':[listener2]}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([listener2], handler.listeners('event2'));

    handler.unbind('event1');

    deepEqual({'event1':[], 'event2':[listener2]}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([listener2], handler.listeners('event2'));
});


QUnit.test('creme.component.EventHandler.unbind (multiple key, all listeners)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1'),
        listener2 = this.mockListener('2');

    handler.bind('event1', listener);
    handler.bind(['event1', 'event2'], listener2);

    deepEqual({'event1':[listener, listener2], 'event2':[listener2]}, handler._listeners);
    deepEqual([listener, listener2], handler.listeners('event1'));
    deepEqual([listener2], handler.listeners('event2'));

    handler.unbind(['event1', 'event2']);

    deepEqual({'event1':[], 'event2':[]}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));

    handler.unbind(['event1', 'event2']);

    deepEqual({'event1':[], 'event2':[]}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));
});

QUnit.test('creme.component.EventHandler.unbind (split key, all listeners)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1'),
        listener2 = this.mockListener('2');

    handler.bind('event1', listener);
    handler.bind(['event1', 'event2'], listener2);

    deepEqual({'event1':[listener, listener2], 'event2':[listener2]}, handler._listeners);
    deepEqual([listener, listener2], handler.listeners('event1'));
    deepEqual([listener2], handler.listeners('event2'));

    handler.unbind(['event1 event2']);

    deepEqual({'event1':[], 'event2':[]}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));

    handler.unbind(['event1 event2']);

    deepEqual({'event1':[], 'event2':[]}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));
});

QUnit.test('creme.component.EventHandler.unbind (dict)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listeners = {
            event1: this.mockListener('1'),
            event2: [this.mockListener('2'), this.mockListener('3')]
        }

    handler.bind(listeners);

    deepEqual({'event1':[listeners.event1], 
               'event2':[listeners.event2[0], listeners.event2[1]]}, handler._listeners);

    handler.unbind(listeners);

    deepEqual({'event1':[], 'event2':[]}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));

    handler.unbind(listeners);

    deepEqual({'event1':[], 'event2':[]}, handler._listeners);
    deepEqual([], handler.listeners('event1'));
    deepEqual([], handler.listeners('event2'));
});

QUnit.test('creme.component.EventHandler.unbind (dict array)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listeners1 = {
            event1: this.mockListener('1'),
            event2: [this.mockListener('2'), this.mockListener('3')]
        },
        listeners2 = {
            event1: this.mockListener('2.1'),
            event3: [this.mockListener('2.2'), this.mockListener('2.3')]
        };

    handler.bind([listeners1, listeners2]);

    deepEqual({'event1':[listeners1.event1, listeners2.event1], 
               'event2':[listeners1.event2[0], listeners1.event2[1]],
               'event3':[listeners2.event3[0], listeners2.event3[1]]}, handler._listeners);

    handler.unbind([listeners1, listeners2]);

    deepEqual({'event1':[], 'event2':[], 'event3':[]}, handler._listeners);

    handler.unbind([listeners1, listeners2]);

    deepEqual({'event1':[], 'event2':[], 'event3': []}, handler._listeners);
});

QUnit.test('creme.component.EventHandler.error', function(assert) {
    var handler = new creme.component.EventHandler();
    var handled_error = null;
    var invalid_listener = function() {
        throw Error('event handler error !');
    };

    equal(true, Object.isFunc(handler.error()));

    handler.on('event1', invalid_listener);
    handler.error(function(e, key, args, listener) {
        handled_error = {
            error: e,
            event: key,
            args: args,
            listener: listener,
            source: this
        };
    });

    handler.trigger('event1', 'a');

    equal('event1', handled_error.event);
    deepEqual(['a'], handled_error.args);
    equal(invalid_listener, handled_error.listener);
    equal(handler, handled_error.source);
    equal('Error: event handler error !', String(handled_error.error));
});

QUnit.test('creme.component.EventHandler.error (disable)', function(assert) {
    var handler = new creme.component.EventHandler();
    var handled_error = null;
    var error_listener = function() {
        throw Error('event handler error !');
    };

    equal(true, Object.isFunc(handler.error()));

    handler.on('event1', error_listener);
    handler.error(function(e, key, args, listener) {
        handled_error = {
            error: e,
            event: key,
            args: args,
            listener: listener,
            source: this
        };
    });

    handler.trigger('event1', 'a');
    equal('event1', handled_error.event);

    handled_error = null;
    handler.error(null); // disable error handler !

    handler.trigger('event1', 'a');
    equal(null, handled_error); // nothing happens !
});

QUnit.test('creme.component.EventHandler.error (not a function)', function(assert) {
    var handler = new creme.component.EventHandler();

    this.assertRaises(function() {
        handler.error('not a function');
    }, Error, 'Error: event error handler is not a function');
});

QUnit.test('creme.component.EventHandler.one (single key, single listener)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1'),
        listener2 = this.mockListener('2');

    handler.one('event1', listener);
    handler.bind('event1', listener2);

    assertListenerUUIDs(handler.listeners('event1'), [listener, listener2]);

    deepEqual([], this._eventListenerCalls);

    handler.trigger('event1', 'a');
    deepEqual([['1', handler, 'event1', 'a'], ['2', handler, 'event1', 'a']], this._eventListenerCalls, 'calls');

    assertListenerUUIDs(handler.listeners('event1'), [listener2]);

    this.resetMockCalls();
    handler.trigger('event1', 'a');
    deepEqual([['2', handler, 'event1', 'a']], this._eventListenerCalls, 'calls');

    assertListenerUUIDs(handler.listeners('event1'), [listener2]);
});

QUnit.test('creme.component.EventHandler.one (single key, multiple listeners)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1'),
        listener2 = this.mockListener('2'),
        listener3 = this.mockListener('3');

    handler.one('event1', [listener, listener2]);
    handler.bind('event1', listener3);

    assertListenerUUIDs(handler.listeners('event1'), [listener, listener2, listener3]);

    deepEqual([], this._eventListenerCalls);

    handler.trigger('event1', 'a');
    deepEqual([['1', handler, 'event1', 'a'], ['2', handler, 'event1', 'a'], ['3', handler, 'event1', 'a']], this._eventListenerCalls, 'calls');

    assertListenerUUIDs(handler.listeners('event1'), [listener3]);
});

QUnit.test('creme.component.EventHandler.one (multiple key, single listener)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1'),
        listener2 = this.mockListener('2');

    handler.one(['event1', 'event2'], listener);
    handler.bind(['event1', 'event2'], listener2);

    assertListenerUUIDs(handler.listeners('event1'), [listener, listener2]);
    assertListenerUUIDs(handler.listeners('event2'), [listener, listener2]);

    deepEqual([], this._eventListenerCalls);

    handler.trigger('event1', 'a');
    deepEqual([['1', handler, 'event1', 'a'], ['2', handler, 'event1', 'a']], this._eventListenerCalls, 'calls');

    assertListenerUUIDs(handler.listeners('event1'), [listener2]);
    assertListenerUUIDs(handler.listeners('event2'), [listener, listener2]);

    this.resetMockCalls();
    handler.trigger('event1', 'a');
    deepEqual([['2', handler, 'event1', 'a']], this._eventListenerCalls, 'calls');

    assertListenerUUIDs(handler.listeners('event1'), [listener2]);
    assertListenerUUIDs(handler.listeners('event2'), [listener, listener2]);

    this.resetMockCalls();
    handler.trigger('event2', 12);
    deepEqual([['1', handler, 'event2', 12], ['2', handler, 'event2', 12]], this._eventListenerCalls, 'calls');

    assertListenerUUIDs(handler.listeners('event1'), [listener2]);
    assertListenerUUIDs(handler.listeners('event2'), [listener2]);
});

QUnit.test('creme.component.EventHandler.one (multiple key, multiple listeners)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1'),
        listener2 = this.mockListener('2'),
        listener3 = this.mockListener('3');

    handler.one(['event1', 'event2'], [listener, listener2]);
    handler.bind(['event1', 'event2'], listener3);

    assertListenerUUIDs(handler.listeners('event1'), [listener, listener2, listener3]);
    assertListenerUUIDs(handler.listeners('event2'), [listener, listener2, listener3]);

    deepEqual([], this._eventListenerCalls);

    handler.trigger('event1', 'a');
    deepEqual([['1', handler, 'event1', 'a'], ['2', handler, 'event1', 'a'], ['3', handler, 'event1', 'a']], this._eventListenerCalls, 'calls');

    assertListenerUUIDs(handler.listeners('event1'), [listener3]);
    assertListenerUUIDs(handler.listeners('event2'), [listener, listener2, listener3]);

    this.resetMockCalls();
    handler.trigger('event1', 'a');
    deepEqual([['3', handler, 'event1', 'a']], this._eventListenerCalls, 'calls');

    assertListenerUUIDs(handler.listeners('event1'), [listener3]);
    assertListenerUUIDs(handler.listeners('event2'), [listener, listener2, listener3]);

    this.resetMockCalls();
    handler.trigger('event2', 12);
    deepEqual([['1', handler, 'event2', 12], ['2', handler, 'event2', 12], ['3', handler, 'event2', 12]], this._eventListenerCalls, 'calls');

    assertListenerUUIDs(handler.listeners('event1'), [listener3]);
    assertListenerUUIDs(handler.listeners('event2'), [listener3]);
});

QUnit.test('creme.component.EventHandler.one ()', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1'),
        listener2 = this.mockListener('2');

    handler.one('event1', listener);
    handler.bind('event1', listener2);
    handler.one('event2', listener);

    assertListenerUUIDs(handler.listeners('event1'), [listener, listener2]);
    assertListenerUUIDs(handler.listeners('event2'), [listener]);

    deepEqual([], this._eventListenerCalls);

    handler.trigger('event1', 'a');
    deepEqual([['1', handler, 'event1', 'a'], ['2', handler, 'event1', 'a']], this._eventListenerCalls, 'calls');

    assertListenerUUIDs(handler.listeners('event1'), [listener2]);
    assertListenerUUIDs(handler.listeners('event2'), [listener]);

    this.resetMockCalls();
    handler.trigger('event2', 12);

    assertListenerUUIDs(handler.listeners('event1'), [listener2]);
    assertListenerUUIDs(handler.listeners('event2'), []);

    deepEqual([['1', handler, 'event2', 12]], this._eventListenerCalls, 'calls');

    this.resetMockCalls();
    handler.trigger('event2', 12);

    assertListenerUUIDs(handler.listeners('event1'), [listener2]);
    assertListenerUUIDs(handler.listeners('event2'), []);

    deepEqual([], this._eventListenerCalls, 'calls');
    
    this.resetMockCalls();
    handler.trigger('event1', 12);

    assertListenerUUIDs(handler.listeners('event1'), [listener2]);
    assertListenerUUIDs(handler.listeners('event2'), []);

    deepEqual([['2', handler, 'event1', 12]], this._eventListenerCalls, 'calls');
});

QUnit.test('creme.component.EventHandler.one (decorator)', function(assert) {
    var handler = new creme.component.EventHandler();
    var listener = this.mockListener('1');
    var decorator_listeners = {
         'event1-pre': this.mockListener('1a'),
         'event1-post': this.mockListener('1b')
    };

    var decorator = function(key, listener, args) {
        handler.trigger(key + '-pre', Array.copy(args, 1));
        listener.apply(this, args);
        handler.trigger(key + '-post', Array.copy(args, 1));
    }

    handler.on(decorator_listeners);
    handler.one('event1', listener, decorator);
    handler.trigger('event1', 'a');

    deepEqual([['1a', handler, 'event1-pre', 'a'],
               ['1', handler, 'event1', 'a'],
               ['1b', handler, 'event1-post', 'a']], this._eventListenerCalls, 'calls');

    this.resetMockCalls();
    handler.trigger('event1', 'a');

    deepEqual([], this._eventListenerCalls, 'calls');
});
