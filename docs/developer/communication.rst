Extend server/client communication protocol
===========================================

Add a request
-------------

To handle a new request, you must first create a new request class that you can add into module
:mod:`diplomacy.communication.requests`. You request may be:

- a public request, which must directly inherit from :class:`_AbstractRequest`.
- a channel request, which must inherit from :class:`_AbstractChannelRequest`.
- a gme request, which must inherit from :class:`_AbstractGameRequest`.

Then your request must be handled by the server. To do that:

- create a request handler method. Recommended name is `on_<REQUEST_SNAKE_NAME>`. Signature must be
  ``on_<REQUEST_SNAKE_NAME>(server, request, connection_handler) -> response`` with:

  - server: instance of :class:`diplomacy.server.server.Server` object representing the server receiving the request.
  - request: received request, which will be an instance of your request class.
  - connection_handler: the :class:`diplomacy.server.connection_handler.ConnectionHandler` object managing the
    websockets connection from which the server receives the request. It is generally not used.
  - response: your handler must return the response to send to client. Response can be, either:

    - ``None``. In such case, server will automatically send a :class:`.OK` response to client.
    - explicit :class:`.Ok` reponse.
    - a :class:`.NoResponse` response. In such case, server will send nothing to client. This can be used if the
      request is intended to act like a "client notification", where client does not expect any response.
    - a specific data response. You can either choose one of responses already defined in module
      :mod:`diplomacy.communication.responses`, or create your own data response by inheriting from class
      :class:`_AbstractResponse`.

    Response classes are generally added into module :mod:`diplomacy.communication.responses`.

  Request handlers are generally added into module :mod:`diplomacy.server.request_managers`
- Register your request handler by adding an entry mapping your request class to your handler into dictionary
  :const:`diplomacy.server.request_managers.MAPPING`.

.. warning::

    Your request handler must **not** return an :class:`diplomacy.communication.responses.Error` response.
    This is a special response class used by server to send an error to client.
    Instead, if your request handler detects any error, it must raise a proper
    exception inheriting from :class:`.ResponseException`.

Once server handles the request, client must then be able to send the request and handle the response.
For python client, you must first add the remote method that will send the request to the appropriate class:

- if your request is a public request, remote method should be added to class :class:`.Connection`. See
  :meth:`.Connection.authenticate` as an example of how to add a remote method to connection class.
- if your request is a channel request, remote method should be added to class :class:`.Channel`. This is generally
  done by adding a static member to channel class using function :func:`.req_fn` with request class and optional
  predefined request parameters as function arguments. Check channel class to see how other remote methods are defined.
- if your request is a game request, you must first add a remote method to class :class:`.Channel` for this request,
  and then add a remote method in class :class:`.NetworkGame` that will call corresponding channel method. This is
  generally done by adding a statc member network game class using function :func:`.game_request_method` with
  channel method as function argument. Check network game class to see how other remote methods are defined.

Request can now be sent from client. The ultimate step is to handle the server response. To do that:

- create a response handler method. Recommended name is ``on_<REQUEST_SNAKE_NAME>``. Signature must be
  ``on_<REQUEST_SNAKE_NAME>(context, response) -> retval`` with:

  - context: the :class:`.RequestFutureContext` object containing the request associated to response.
  - response: the response object received, which will be identical to the response object sent by server.
  - retval: your handler can return a value, which will be the ultimate value returned by the remote method
    you defined in client. It's whatever you want, or ``None`` if you don't want remote metho to return anything.

  Response handler are generally added into module :mod:`diplomacy.client.response_managers`.
- Register your response handler by adding entry mapping the request class to your response handler into dictionary
  :const:`diplomacy.client.response_managers.MAPPING`

Add a notification
------------------

To handle a new notification, you must first create the notification class, which can be added to module
:mod:`diplomacy.communication.notifications`. Your notification may be:

- a channel notification, which must inherit from :class:`._ChannelNotification`.
- a game notification, which must inherit from :class:`._GameNotification`.

Notifications are usually sent into server request handlers by instanciating the class :class:`.Notifier` and
calling an appropriate method. Then, to be able to send the new notification, you must add a dedicated method into
class :class:`.Notifier`. The method should receive relevant arguments to build notification objects, and then it
can call method :meth:`.Notifier._notify` to effectively send a notification object. Notifier also provides some
helper methods you can use, for example :meth:`.Notifier._notify_game` to notify all users involved in a game.

Once server can send the notification, it should be handled on client side. For python client, you must:

- create a notification handler method. Recommended name is ``on_<NOTIFICATION_SNAKE_NAME>``. Signature must be either
  ``on_<NOTIFICATION_SNAKE_NAME>(channel, notification)`` for a channel notification, or
  ``on_<NOTIFICATION_SNAKE_NAME>(game, notification)`` for a game notification. ``channel`` is the channel object
  receiving the notification, ``game`` is the game receiving the notification, and ``notification`` is the
  received notification. Handler should return nothing. Notification handlers are generally added into module
  :mod:`diplomacy.client.notification_managers`.
- Register your notification handler by adding entry mapping the notification class to your notification handler
  into dictionary :const:`diplomacy.client.notification_managers.MAPPING`.

Ultimately, if your notification is a game notification, you can update the :class:`.NetworkGame` to allow callback
to be added to game for this notification. To do that, create static member ``add_on_<notification_snake_name>``
(to add callback) using fonction :func:`.callback_setting_method` with notification class as argument, and
static member ``clear_on_<notification_snake_name>`` (to clear callback) using function
:func:`.callback_clearing_method` with notification class as argument.
