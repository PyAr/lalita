Lalita
======

¿Quién es Lalita?
-----------------

Lalita es un bot de IRC al que de forma sencilla se le pueden agregar plugins
con nuevas funcionalidades.  El objetivo es que sea muy fácil implementar lo
que uno necesite en un bot.

En otras palabras, Lalita es un framework que nos permite armar nuestro bot
IRC a medida, de manera sencilla y rápida.  Como si eso fuera poco, además
tenemos algunos plugins que vienen incluidos (ver abajo).


¿Qué es un bot IRC?
-------------------

Un bot IRC es un programa que entra en algún canal en algún servidor de
IRC_ (o a muchos canales en un servidor, o a muchos servidores, etc.), y
se comporta como un miembro más del canal.

La idea de un bot IRC no es hacerse pasar por un ser humano conectado (la
mayoría de las veces), sino prestar determinados servicios a los usuarios
del canal (la palabra 'bot' es un diminutivo de 'robot').

La prestación de estos servicios involucra que el bot reciba de alguna manera
lo que la gente dice, y que les conteste.  A lo largo de los siguientes
ejemplos veremos distintas formas de hacer esto.


Un ejemplo básico
=================

En esta sección armaremos un plugin sencillo que suma los números que dice
una persona al hablarle al bot.

El siguiente es el código en cuestión::

    # -*- coding: utf8 -*-

    from lalita import Plugin

    class Sum(Plugin):
        """Ejemplo que suma los nros pasados."""

        def init(self, config):
            self.register(self.events.TALKED_TO_ME, self.action)

        def action(self, user, channel, msg):
            u"Suma los números recibidos."
            result = sum(int(x) for x in msg.split())
            self.say(channel, u"%s, la suma es %d", user, result)

Vemos que el plugin se implementa como una clase de Python que hereda de
Plugin (el cual es importado arriba de todo).  El heredar de esta clase nos
permite acceder a toda la funcionalidad básica necesaria para armar nuestro
plugin, como veremos en los próximos párrafos.

Esta clase será instanciada por el sistema para cada canal o servidor, y en
el momento de instanciar se le pasará una configuración (en este caso no
la usamos, ver abajo más info sobre esto).  El momento de la instanciación
es el adecuado para que el plugin se registre en los eventos que desea
escuchar; en este ejemplo sólo nos registramos a un sólo evento,
``TALKED_TO_ME``, y le decimos que en ese caso nos ejecute un determinado
método.

Analicemos esa linea con más detalle::

    self.register(self.events.TALKED_TO_ME, self.action)

El método ``self.register`` es el que usamos para registrarnos en un
evento.  Al mismo le pasaremos al menos dos parámetros (ver más abajo para
una descripción detallada de todos los casos), el evento y un método propio.

En este caso el evento es ``TALKED_TO_ME``, que sucede cuando en el canal
se le habla al bot, y se accede a través del atributo ``self.events``.  Y
el método que le decimos que ejecute es ``self.action``, que definimos ahí
mismo en el ejemplo.

Este método no tiene demasiadas restricciones, pero hay que prestar atención
a los parámetros declarados, porque dependen de cada evento.  Para el evento
con el que estamos trabajando, el método recibirá el usuario que nos dijo
algo, el canal en el que se dijo, y el mensaje en cuestión.

Luego de calcular el resultado que buscamos (la suma de los números pasados,
calculado de forma simple para no complicar el ejemplo), contestamos al
usuario utilizando otro método heredado: ``self.say``.  Al mismo le
pasamos primero el destino de lo que estamos diciendo (en este caso el
canal por dónde nos hablaron), luego el mensaje que queremos decir, y
finalmente valores para reemplazar en ese mensaje (veremos luego por qué
es importante no reemplazarlos directamente).

Las siguientes lineas muestran el diálogo con el bot (que llamamos
*examplia*) en la vida real::

    <usuario>   examplia, 12 88
    <examplia>  usuario, la suma es 100
    <usuario>   examplia, 4 5 6
    <examplia>  usuario, la suma es 15


¿Pero cómo pruebo eso?
----------------------

Para probar Lalita no hace falta realizar ninguna instalación en particular.
Se puede bajar y descomprimir un tarball, o incluso bajar todo el proyecto
entero haciendo ``bzr branch lp:lalita``, y usarlo directamente.

*FIXME: también se puede instalar con easy_install, mostrar cómo, ver si
tenemos que cambiar algo del texto porque instalado así se usa distinto.*

*FIXME: re-redactar esto! tenemos que arrancar con los tres pasos para
hacerlo funcionar, y luego explicamos qué es cada cosa, de manera que le
sirva también a aquellos que no quieren leer.  Para hacerla más fácil
daremos un ejemplo que se conecte a freenode.*

Entrando al directorio donde está el proyecto, hay tres archivos que tenemos
que considerar para probar el ejemplo.

- El código arriba mostrado grabado en un archivo en el directorio
  ``plugins/``; en nuestro caso lo guardaremos en un archivo llamado
  ``plugins/ejemplodoc.py``.

- El programa principal, que es ``ircbot.py``, y que mostraremos abajo
  cómo ejecutar.

- Un archivo de configuración, ``config.py``.  El proyecto trae un
  ``config.py.example`` con múltiples configuraciones de muestra, pero
  veremos aquí mismo cómo hacer uno básico que nos sirva para probar
  el ejemplo.

La configuración no es más que un diccionario Python con toda la información
necesaria.  Aquí mostramos una configuración muy sencilla. Pueden ver
el ``config.py.example`` para otras configuraciones, y abajo en este
mismo documento para más explicaciones.

En nuestro caso usaremos::

    servers = {
       'example': dict(
           encoding = 'utf8',
           host = 'localhost', port = 6667,
           nickname = 'examplia',
           channels = {
               '#humites': {},
           },
           plugins = {
               'ejemplodoc.Sum': {},
           },
       ),
    }

En este caso tenemos un sólo server configurado, llamado ``example``,
apuntando a localhost en el puerto 6667 (lo más fácil para probar ejemplos
y desarrollar nuestro propio plugin es instalar un servidor de IRC en la
propia computadora. Por ejemplo, se puede utilizar ``dancer-ircd``,
principalmente porque al instalarlo ya queda funcionando como queremos y
no hay que realizar configuraciones adicionales).

En la configuración decimos que el nick del bot será ``examplia``, y
utilizará UTF-8 como encoding, y nos conectaremos al canal ``#humites``,
instanciando al plugin que acabamos de crear (notar que la forma de
especificar al plugin es ``archivo.Clase`` (sin el ``.py``), lo que nos da la
libertad de tener varios plugins en distintos archivos y sólo especificar
el que queremos usar.

Una vez grabado el config.py, probamos todo haciendo::

  python ircbot.py example

Usamos ``python`` para llamar al intérprete, ``ircbot.py`` para ejecutar
Lalita, y ``example`` para indicarle cual de los servidores configurados
vamos a utilizar (podemos tener muchos configurados y usar algunos
solamente).  Se muestra solamente la forma de ejecución más simple, ver
abajo distintas opciones que se pueden utilizar en cada caso.


Usando ordenes
==============

Normalmente, para la funcionalidad del ejemplo anterior, se hubiese usado una
orden (o *comando*).

Usar ordenes nos permite ejecutar determinadas funcionalidades del bot sin
tener que hablarle directamente.  Los comandos se identifican porque comienzan
con un ``@`` al principio; entonces, lo que buscamos es poder hacer lo
siguiente::

    <usuario>   @sumar 12 88
    <examplia>  usuario, la suma es 100
    <usuario>   @sumar 4 5 6
    <examplia>  usuario, la suma es 15

Vemos que no le hablamos al bot directamente, sino que usamos el comando
``contar``.  Modificamos ligeramente nuestro código anterior para poder
implementar esta orden::

    # -*- coding: utf8 -*-

    from lalita import Plugin

    class Sum(Plugin):
        """Ejemplo que suma los nros pasados."""

        def init(self, config):
            self.register(self.events.COMMAND, self.action, ("sumar",))

        def action(self, user, channel, command, *args):
            u"Suma los números recibidos."
            result = sum(int(x) for x in args)
            self.say(channel, u"%s, la suma es %d", user, result)

Vemos que cambió la linea de registración.  Ahora nos registramos a otro
evento, y además pasamos más datos: una tupla con los comandos a registrar
(``sumar``, que es lo que usamos arriba con el ``@``).

También cambió la signatura de la función, ahora se recibe el usuario y
el canal (como antes), más el comando con el que llegamos ahí, más todos
los parámetros pasados al comando (notar que la forma de calcular el
resultado varía ligeramente, ya que la info la recibimos preprocesada
en este caso).


Múltiples comandos para una misma funcionalidad
-----------------------------------------------

Es normal la necesidad de proveer la misma funcionalidad para distintos
comandos.  Esto viene de la necesidad de soportar el comando en dos idiomas,
o para compatibilidad con formas viejas de escribirlo.

Lalita está preparada para soportar esto de forma sencilla, ya que a la hora
de registrar un método podemos hacerlo para distintos comandos.  Veamos esto
en funcionamiento; modifiquemos la linea de registración del ejemplo anterior
para que diga::

        self.register(self.events.COMMAND, self.action,
                      ("suma", "sumar", "sum"))

Entonces, podemos usar cualquiera de esos comandos::

    <usuario>   @sumar 12 3
    <examplia>  usuario, la suma es 15
    <usuario>   @suma 12 3
    <examplia>  usuario, la suma es 15
    <usuario>   @sum 12 3
    <examplia>  usuario, la suma es 15


Ordenes genéricas del bot
-------------------------

Lalita tiene sus propios metacomandos que nos permite acceder a funcionalidad
que va más allá de los plugins instalados.

Las ordenes intrínsecas a Lalita misma son ``help``, ``list`` y ``more``.

El primero nos da un mensaje genérico, o la ayuda específica de un
determinado comando.  El segundo nos lista todos los comandos disponibles.
Vemos una ejemplo de uso de estos en las siguientes lineas::

    <usuario>   @help
    <examplia>  "list" para ver las ordenes; "help cmd" para cada uno
    <usuario>   @list
    <examplia>  Las ordenes son: ['help', 'list', 'more', 'sum', 'suma', 'sumar']
    <usuario>   @help sumar
    <examplia>  Suma los números recibidos.

En la lista de ordenes vemos que tenemos los metacomandos más todos los
comandos que nosotros registramos (incluso si apuntan al mismo método dentro
de nuestro código).  ¿Pero de dónde viene la ayuda que Lalita muestra para
nuestros comandos?  Si prestaron la suficiente atención verán que para
esto se utiliza el docstring del método implementado.

Si prestaron atención, también habrán notado que nombré tres metacomandos
arriba, pero expliqué solamente dos.  Nos queda el tercero: ``more``.  Esta
es una orden utilizada sólo en casos muy específicos: cuando entra en acción
una regulación de Lalita para comportarse decentemente en un canal.

Veremos luego que hay formas de contestar más de una linea en una orden,
lo cual es muy útil si uno quiere implementar funciones de búsquedas, por
ejemplo.  ¿Pero qué pasaría si el plugin contesta con muchos resultados,
digamos... 1000?  Lo normal es que el servidor de IRC nos eche por
*flood* (ya que inundaríamos a todos los usuarios con un sin fin de
lineas; esta protección está implementada en la mayoría de los
servidores).  Entonces Lalita tiene un mecanismo para que el plugin no
pueda caer en este error.

Si el plugin contesta muchas lineas al mismo canal o usuario, sólo pasan
las primeras 5 y el resto se encola y no se muestran a menos que el mismo
usuario que generó el comando original diga ``@more``, haciendo que Lalita
muestre las próximas 5 lineas encoladas, y así hasta que se acabe lo
encolado, el usuario diga otra cosa, o pase un determinado tiempo que hace
caducar a la cola de respuestas.

*FIXME: indicar cómo se configura ese "5" para que no sea mágico.*


¿Cuales son los eventos que podemos recibir?
============================================

Los plugins pueden recibir muchos eventos. La siguiente lista los agrupa por
el tipo de suceso que el evento informa, mostrando los parámetros que se
envían en cada caso y una pequeña descripción de qué significa.

Eventos referentes a la conexión del bot contra el server:

- ``CONNECTION_MADE []``: La conexión está establecida contra el servidor.

- ``CONNECTION_LOST []``: La conexión se terminó.

- ``SIGNED_ON []``: Ya se identificó correctamente con el server.

- ``JOINED [canal]``: El plugin ya se unió al canal indicado.

Eventos que indican personas hablando:

- ``PRIVATE_MESSAGE [usuario, mensaje]``: Algo dicho a Lalita por privado (no
  en un canal público).

- ``TALKED_TO_ME [usuario, canal, mensaje]``: Algo dicho en el canal, pero
  específicamente a Lalita.

- ``PUBLIC_MESSAGE [usuario, canal, mensaje]``: Algo dicho en el canal, de
  forma genérica.

- ``COMMAND [usuario, canal, comando, parámetros]``: Un comando generado en el
  canal, especificando el comando y los argumentos al mismo.

Eventos que representan acciones de los usuarios o hacia los usuarios.

- ``ACTION [usuario, canal, mensaje]``: El usuario generó una acción en el
  canal (por ejemplo, "/me").

- ``JOIN [usuario, canal]``: El usuario se sumó al canal en cuestión.

- ``LEFT [usuario, canal``: El usuario abandonó el canal en cuestión.

- ``QUIT [usuario, mensaje]``: El usuario se desconectó del servidor
  completamente, indicando un determinado mensaje de salida.

- ``KICK [pateado, canal, pateador, mensaje]``: El usuario fue pateado del
  canal, por una determinado operador ("pateador"), con un determinado mensaje.


Registrando eventos
===================

Ya vimos el mecanismo básico para que un plugin registre métodos para que
sean llamados ante determinados eventos.  Aquí mostraremos todas las
combinaciones posibles que podemos lograr.

Como decíamos, el mecanismo básico de registración es::

    self.register(<evento>, <método>)

La mayoría de los eventos permiten solamente eso.  Pero en algunos casos
podemos especificar otros parámetros.

*FIXME: explicar qué sucede si te registrás dos veces.*


Múltiples comandos
------------------

En el caso del evento COMMAND, se debe especificar una tupla con todos los
nombres de comandos u ordenes que se registrarán para el método en cuestión.
Esto nos permite especificar varios comandos para un determinado método, y
varios métodos para determinados comandos, como se muestra en las
siguientes lineas::

    self.register(self.events.COMMAND, self.sum, ("sumar", "sum"))
    self.register(self.events.COMMAND, self.multiply, ("mult", "multiply"))
    self.register(self.events.COMMAND, self.divide, ("div",))

*FIXME: no hay ejemplo para "varios métodos para un determinado comando".*


Filtrando los mensajes
----------------------

En el caso de los eventos ``TALKED_TO_ME``, ``PRIVATE_MESSAGE``,
y ``PUBLIC_MESSAGE``, se le puede especificar una expresión regular
para que Lalita filtre la cantidad de mensajes que generan este
tipo de evento.  De esta manera, nuestro plugin no recibiría todos los
mensajes de este tipo (que potencialmente podrían ser muchos, ya
que ``PUBLIC_MESSAGE`` implica todo el tráfico del canal), sino
solamente aquellos ya filtrados.

Un ejemplo de esto sería la siguiente registración::

        regex = re.compile(".*http://.*")
        self.register(self.events.PUBLIC_MESSAGE, self.action, regex)

Entonces nuestro método ``self.action`` no recibiría todos los mensajes
públicos, sólo aquellos que tengan ``http://`` en el mensaje.

Prestar atención que no se pasa la cadena directamente, sino una expresión
regular compilada.  Esto es por flexibilidad: realmente podríamos pasar
no solamente una expresión regular, sino que tenemos la posibilidad de
pasar cualquier objeto que preparemos que tenga el método ``.match()``
(si devuelve algo que evalúa a ``True``, se pasa el mensaje al plugin,
sino no).


Comandos automáticos
--------------------

Es más sencillo y directo para los usuarios del bot, en algunos casos, el
poder especificar el comando hablando directamente con el bot, ya sea de
forma privada o pública (y no solamente usando el ``@`` al principio).

Por ejemplo, si nosotros tenemos registrado el comando ``sumar``, como en
el ejemplo anterior, podríamos tener el siguiente diálogo::

    <usuario>   @sumar 12 3
    <examplia>  usuario, la suma es 15
    <usuario>   examplia, sumar 12 3
    <examplia>  usuario, la suma es 15

Esto lo podríamos hacer a mano (recibiendo todos los eventos públicos y
privados y filtrando), pero Lalita ya nos ofrece esta funcionalidad integrada.

Para activarla, sólo tenemos que hacer::

        self.set_options(automatic_command=True)

*FIXME: no vamos a tener set_options, todas las opciones serán manejadas
desde la config.*

De esta manera, todos los eventos ``TALKED_TO_ME`` y ``PRIVATE_MESSAGE``
que tengan un mensaje que comiencen con un comando registrado, serán
modificados y enviados al plugin como si hubiese sido justamente una
orden, y no un evento de esos tipos.


Hablando con más libertad
=========================

En un capítulo anterior mostramos el uso básico de ``self.say``, que es la
herramienta que tienen los plugins para decir cosas a los usuarios.

La sintaxis de esta herramienta es sencilla::

    self.say(<destino>, <texto>, [<arg1>, ...])

El destino es a quien va dirigido el mensaje.  Si es un usuario, el mensaje
será privado.  Si es un canal (que empieza por ``#``), el mensaje será dicho
en el canal público (aquí Lalita aplica una restricción: el plugin solo
puede contestar algo por el mismo canal que se le preguntó o en
privado, pero no puede cruzar respuestas de canales).

El segundo parámetro es el texto del mensaje que queremos comunicar.  No hay
a priori una restricción de longitud, pero los textos muy largos se
transforman a varias lineas, por restricciones propias de IRC.  Se
recomienda que el texto sea siempre una cadena Unicode, incluso si en
el mensaje no estamos utilizando caracteres no ASCII.

Si queremos componer el mensaje con algunos parámetros (como el nombre
del usuario o el resultado de la suma en el ejemplo anterior), NO debemos
hacer el reemplazo directamente, sino armar la cadena como corresponde y
pasar los argumentos luego del texto.

En otras palabras, y siguiendo con el ejemplo anterior, se recomienda NO
hacer lo siguiente::

        self.say(channel, u"%s, la suma es %d" % (user, result))

Se debe hacerlo de esta manera::

        self.say(channel, u"%s, la suma es %d", user, result)

Hay dos razones para esto.  La primera es que en caso de tener una cantidad
incorrecta de parámetros o tipos de datos incorrectos en la conversión,
esto se puede manejar mejor por Lalita.  La segunda y más importante es que
al no reemplazar los valores, podemos hacer que nuestros textos sean
internacionalizables (ver abajo más detalle sobre esto).


Siendo verborrágicos
--------------------

No hay ninguna restricción sobre la cantidad de lineas que puede contestar
un plugin (más allá del mecanismo de encolado de mensajes para evitar
*flood* que se describió arriba).

Es decir, un plugin puede contestar dos o más lineas, usando varias veces
el ``self.say``, por ejemplo::

        self.say(channel, u"El resultado es %d", result)
        self.say(channel, u"(tiempo de cálculo: %.2f segundos)", t)


Prometiendo respuestas a futuro
-------------------------------

Los métodos de los plugins no deben tardar mucho. Esto se debe a que Lalita
está programada usando un motor de ejecución asincrónico llamado Twisted_,
por lo que las ejecuciones de los métodos no son interrumpibles.

En otras palabras, si un método de un plugin tarda mucho, Lalita no
puede atender el resto de las cosas que tiene que hacer (escuchar
múltiples canales, ejecutar métodos de otros plugins, etc.).

Entonces, ¿cómo hacemos si tenemos que acceder a servicios que
potencialmente pueden tardar mucho, como base de datos, o usar la red?
Aquí es donde entra en juego un mecanismo de Twisted llamado Deferreds_.

Pueden buscar algo de documentación sobre Deferreds en ese enlace, y
revisar en el plugin de ejemplo (``plugins/example.py``) cómo se
implementa esto, pero básicamente el proceso es: en lugar de hacer
``self.say()`` y contestar algo, la ejecución del método devuelve al
terminar una promesa a futuro.

Esta promesa a futuro es el *deferred*, que se consumirá cuando el
plugin esté listo para contestar.  Realmente el plugin puede devolver o
no el deferred, ya que el funcionamiento será el mismo, pero si al usar
un deferred el plugin lo devuelve, Lalita lo usará para loguear la
finalización exitosa o por error del mismo.


Hablando sin contestar
----------------------

*FIXME: quizás pongamos que el default es "hablar libre", y que se puede
configurar para que te restrinja. Deberíamos re-redactar esto acá si fuese
así*

Como mencionamos antes, hay una regla básica que Lalita fuerza para todos
los plugins: estos mismos sólo pueden contestar por el canal que se les
habló (o a la persona en privado que originó el diálogo).  Esta es una
regla de seguridad, que ha probado ser útil, pero al mismo tiempo
restringe algunos comportamientos que desearíamos para un plugin
específico (como poder decirle a un plugin que avise algo importante en
todos los canales en donde está Lalita).

Un efecto secundario de esta limitación es que Lalita no puede decir algo
sin que le hablen primero, y también hay casos de uso en lo que esto sería
deseable, como tener un plugin que informe de noticias nuevas que reciba
por RSS, por ejemplo.

Si necesitamos cualquiera de estas dos funcionalidades, debemos desactivar esta
restricción, de la siguiente manera::

        self.set_options(free_talk=True)

*FIXME: no vamos a tener set_options, todas las opciones serán manejadas
desde la config.*

Luego de esa configuración, podremos generar los mensajes que deseemos
desde el plugin, a cualquier destino, y sin importar si nos hablaron
primero o no.


Armando un plugin más profesional
=================================

Más allá de que armar un plugin sea sencillo, implementar una determinada
funcionalidad de manera robusta y preparada para distribuir en varios
idiomas, o dejarla corriendo 7x24 como servicio confiable, implica
tener algunas precauciones y utilizar algunos mecanismos para hacer
de nuestro programa algo más profesional.


Logueando
---------

Una herramienta que nos ofrece Lalita es la de poder loguear información
(que irá a disco o pantalla en función de configuraciones más generales,
ver abajo).  Para esto tenemos en nuestros plugins a ``self.logger``,
al que podemos usar con distintos grados de severidad, ejemplo::

        self.logger.debug("Recibimos un mensaje de %s", user)
        self.logger.error("Error interno al procesar el pedido")

Los distintos niveles a los que tenemos acceso son ``debug``, ``info``,
``warning``, ``error`` y ``critical``.  Estos niveles son los clásicos
del `módulo logging de Python`_.


Documentando nuestros métodos
-----------------------------

Los docstrings de los métodos de nuestros plugins, que nosotros utilizamos
para implementar funcionalidad, son interpretados automáticamente por
Lalita como la documentación de ayuda para ofrecer al usuario.

Si nos fijamos en nuestro ejemplo anterior, nosotros teníamos nuestro
método que sumaba los números que le pasábamos al bot a través del
comando ``sumar``::

    def action(self, user, channel, command, *args):
        u"Suma los números recibidos."
        ...

El usuario, entonces, puede hacer...::

    <usuario>   @help sumar
    <examplia>  Suma los números recibidos.

...y recibir directamente la documentación que escribimos.

Se recomienda que estos docstrings sean cadenas Unicode.  También,
estos docstrings son internacionalizables de la manera que
explicamos a continuación.


Internacionalizando nuestros textos
-----------------------------------

Lalita tiene un mecanismo de internacionalización que difiere del estándar
seguido por todos los programas.  Esto es debido a que de la forma estándar
la ejecución del programa seguiría un lenguaje determinado, mientras que
Lalita puede estar hablando un idioma en un canal, y otro idioma en otro
canal o servidor.

En nuestro caso, el plugin debe proveer una tabla de traducción,
registrándola de la siguiente manera::

        self.register_translation(self, TABLA_TRADUCCION)

Esta tabla de traducción es sencillamente un diccionario de Python
con la siguiente estructura::

    { <cadena original 1>: { <idioma1> : <cadena 1 en idioma 1>,
                             <idioma2> : <cadena 1 en idioma 2>,
                             ...
                           },
      <cadena original 2>: { <idioma1> : <cadena 2 en idioma 1>,
                             <idioma2> : <cadena 2 en idioma 2>,
                             ...
                           },
      ...
    }

Notar como no es obligatorio escribir las cadenas originales en nuestro
código en ningún idioma en particular, sólo tenemos que proveer las
traducciones a otros idiomas que nos interese en la tabla de traducciones.

Los distintos idiomas 1, 2, etc. mostrados arriba son "en", "it", etc.,
siguiendo las dos letras estándar.  Estas dos letras se utilizan en la
configuración de los canales para que Lalita sepa qué idioma se habla en
cada canal de cada servidor al que se conecte, de manera que ella y
sus plugins hablen ese idioma en cuestión.

Se puede ver una implementación real de esto en el plugin de
ejemplo ``plugins/example.py``.


Configurando el plugin
----------------------

Si prestamos atención al ``config.py`` de ejemplo que utilizamos arriba,
veremos que indicamos que se use el plugin de suma que habíamos escrito::

       plugins = {
           'ejemplodoc.Sum': {},
       },

El diccionario que aquí pasamos vacío puede tener una configuración
totalmente libre, y será pasado por Lalita al plugin en tiempo de
inicialización: el parámetro ``config`` del ``__init__`` es justamente
eso, y nos permite configurar el plugin desde el archivo, sin tener
que implementar mecanismos alternativos.


Algunos plugins que vienen integrados
=====================================

Lalita viene con algunos plugins que implementan funcionalidades
básicas útiles para muchos canales de IRC.

La idea de hacerlos formar parte del proyecto es que si se necesita la
misma funcionalidad o una parecida, no se tenga que arrancar desde cero.
De la misma manera, también pueden servir como ejemplos para ver cómo
realizar determinadas tareas.  Dicho esto, cabe aclarar que la calidad
de los plugins varía un poco: algunos respetan PEP 8 y tienen casos
de prueba en el directorio ``plugins/tests/``, mientras que otros
ni siquiera tienen docstrings...

- example.py: Plugin de ejemplo; no provee ninguna funcionalidad
  específica o útil, pero es un buen ejemplo para ver y copiar.

- freenode.py: Realiza todo el diálogo de autenticación contra los
  servidores de Freenode (debemos configurar algunos parámetros de
  forma adecuada, ver el archivo ``config.py.example``).  Este plugin
  no ofrece ninguna funcionalidad al usuario final, pero nos permite
  conectarnos a estos servidores sin realizar la autenticación nosotros.

- misc.py: Plugin que implementa una funcionalidad muy sencilla: contesta
  "pong" al usuario cuando este le dice "ping" a Lalita.

- seen.py: Implementa dos funcionalidades interesantes: "last" y "seen".
  El primero indica qué fué lo último que dijo un determinado usuario, y
  el segundo nos contesta cuando fue la última vez que el usuario fue
  visto (a veces esto coincide, a veces no).

- url.py: Va juntando todas las URLs que se van mencionando en los
  distintos canales, y luego nos permite buscar en las mismas.


Configuración avanzada
======================

El archivo de configuración de Lalita tiene muchas opciones y es bastante
flexible, así que más allá de inspeccionar el ``config.py.example`` es
interesante una descripción de sus capacidades.  También, al momento de
ejecutar ``ircbot.py`` podemos hacer uso de otras opciones, que se
explican en esta sección.


El archivo de config
--------------------

La estructura del ``config.py`` necesario para que Lalita funcione es
básicamente un gran diccionario de Python.

Las claves de este gran diccionario son los distintos servidores
configurados, los que se especificarán al ejecutar Lalita.  Cada uno de
estos servidores tiene una configuración que también es un diccionario.

El diccionario de cada servidor puede tener las siguientes claves:

 - encoding: La codificación de Unicode que se hablará contra ese servidor
   ("utf8", "latin1", etc.).

 - host: La dirección IP o el nombre del server.

 - port: El puerto del servidor contra el que conectarse.

 - nickname: El nick que tendrá nuestro bot.

 - channels: Los canales a los que entrar en el servidor, más la respectiva
   configuración (ver abajo).

 - plugins: Los plugins (junto con posible configuración) que se ejecutarán a
   nivel de servidor (ver abajo).

 - ssl: En True si debemos usar SSL para conectarnos contra el servidor.

 - password: Una posible palabra clave para el servidor.

 - plugins_dir: El directorio del cual levantar los plugins (si no se
   especifica se toman del directorio ``plugins/`` del proyecto.

El valor de la clave *channels* arriba es un diccionario, donde las claves
son los distintos canales, y el valor correspondiente para cada clave es
la configuración de ese canal, que puede tener dos claves: ``plugins``,
con los distintos plugins habilitados para ese canal (junto con su
diccionario de configuración), y ``encoding``, con la codificación del
canal (si fuese distinta que la del servidor en general).

Podemos notar que los plugins pueden estar descriptos tanto a nivel de
servidor como a nivel de canal.  Ambos casos son útiles y no hay a priori
una regla que indique en donde configurar un determinado plugin.  En
general, ubicaremos un plugin a nivel de canal si es algo específico
para un canal y no queremos que esté disponible para todos; y ubicaremos
un plugin a nivel de servidor cuando es necesario para conectarse
(como el que mencionamos de *freenode*), o lo queremos utilizar también
por privado (ya que cuando dialogamos en privado con un bot estamos
afuera de todo canal).

Por último, cabe notar que es muy difíicil ejemplificar las distintas
combinaciones aquí, pero siempre está el tan mencionado
``config.py.example`` para revisar y tomar de ejemplo.


Parámetros de linea de comando
------------------------------

Cuando ejecutamos a Lalita a través del archivo ``ircbot.py`` tenemos varios
parámetros que nos permiten controlar algunas configuraciones.

La sintaxis general es::

    ircbot.py [-t][-a][-o output_loglvl][-p plugins_loglvl]
              [-f fileloglvl][-n logfname] [server1, [...]]

El argumento *-t* (o *--test*) sirve para realizar pruebas solamente: ejecuta
dos plugins que se conectan a un mismo canal y charlan entre ellos.  Usaremos
esta opción en desarrollo, y no en producción, así que en general la
podemos obviar.

Si pasamos el argumento *-a* (o *--all*), se utilizarán todos los
servidores especificados en ``config.py``, y no se tendrán en cuenta aquellos
indicados en los parámetros de ejecución; por otro lado, si no utilizamos
*-a* tenemos que especificar cual o cuales servidores debe tomar de
la configuración para ejecutarse.

Los argumentos *-o* (*--output-log-level*), *-p* (*--plugin-log-level*)
y *-f* (*--file-log-level*) controlan distintos niveles de logueo, para la
salida en standard output, para filtrar lo recibido de los plugins, y
para escribir en el archivo de log, respectivamente.

El nivel de logueo por default es INFO (con lo que no mostrará todos los
mensajes de DEBUG, por ejemplo).  Podemos configurar cada caso en DEBUG para
ver todo, o en WARNING si solo queremos ver las advertencias y mensajes
más serios, o cualquier combinación que nos plazca.

Con *-n* (o *--log-filename*) especificamos en qué archivo queremos
que se loguee la información que va a un archivo.


.. _IRC: http://es.wikipedia.org/wiki/Internet_Relay_Chat
.. _Twisted: http://twistedmatrix.com/trac/
.. _Deferreds: http://twistedmatrix.com/documents/current/core/howto/defer.html
.. _módulo logging de Python: http://docs.python.org/dev/library/logging.html#logging-levels
