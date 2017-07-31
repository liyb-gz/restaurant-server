# -*- coding: utf-8 -*-

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import cgi
import re
from database_setup import *

welcome_message = 'Hello!'

class WebHandler(BaseHTTPRequestHandler):
	addr = {
		'hello': '/hello',
		'hola': '/hola',
		'res': '/restaurants',
		'res_add': '/restaurants/add'
	}

	pattern = {
		'edit': re.compile(re.escape(addr['res']) + "\/\d*\/edit"),
		'del': re.compile(re.escape(addr['res']) + "\/\d*\/delete"),
		'edit_id': re.compile("(?<=" + re.escape(addr['res']) + "\/)\d*(?=\/edit)"),
		'del_id': re.compile("(?<=" + re.escape(addr['res']) + "\/)\d*(?=\/delete)"),
	}

	html = {
		'not_found': '''
	<html>
		<body>
			<h1>The page you requested cannot be found.</h1>
		</body>
	</html>
''',
		'hello_form': '''
<form action="/hello" method="post" enctype="multipart/form-data">
	<h2>How would you like me to say?</h2>
	<input type="text" name="message"/>
	<input type="submit"  value="submit"/>
</form>
''',
		'restaurant_page': '''
<html>
	<body>
		<h1>Restaurants</h1>
		%s
		%s
	</body>
</html>
''',
		'restaurant_item': '''
	<h2>%s</h2>
	<a href="%s">Edit</a>
	<a href="%s">Delete</a>
	<br>
''',
		'restaurant_add': '''
	<h2>
		<a href="/restaurants/add">Add a new restaurant</a>
	</h2>
''',
		'restaurant_add_page': '''
<html>
	<body>
		<h1>Add A New Restaurant</h1>
		<form action="%s" method="post" enctype="multipart/form-data">
			<input type="text" name="name"/>
			<input type="submit" />
		</form>
	</body>
</html>
''' % addr['res_add'],
		'restaurant_edit_page': '''
<html>
	<body>
		<h1>Rename "%s"</h1>
		<form action="%s" method="post" enctype="multipart/form-data">
			<input type="text" name="name"/>
			<input type="submit" />
		</form>
	</body>
</html>
''',
		'restaurant_del_page': '''
<html>
	<body>
		<h1>Are you sure to delete the restaurant "%s"?</h1>
		<form action="%s" method="post" enctype="multipart/form-data">
			<input type="submit" name="confirm" value="Confirm"/>
			<input type="submit" name="confirm" value="Cancel"/>
		</form>
	</body>
</html>
'''
	}

	DBSession = sessionmaker(bind = engine)

	def path_match(self, pattern):
		return (self.path == pattern) or\
			(self.path == pattern + '/')

	def do_GET(self):
		print self.path
		try:
			if(self.path_match(self.addr['hello'])):
				self.send_response(200)
				self.send_header('Content-Type', 'text/html')
				self.end_headers()

				output = ""
				output += "<html><body>%s %s </body></html>" %\
					(welcome_message, self.html['hello_form'])

				self.wfile.write(output)
				print output

				return

			elif(self.path_match(self.addr['hola'])):
				self.send_response(200)
				self.send_header('Content-Type', 'text/html')
				self.end_headers()

				output = ""
				output += "<html><body> &#161Hola! <a href='/hello'>back to hello.</a> %s </body></html>" % self.html['hello_form']

				self.wfile.write(output)
				print output

				return

			elif(self.path_match(self.addr['res'])):
				self.send_response(200)
				self.send_header('Content-Type', 'text/html')
				self.end_headers()

				# try:
				session = self.DBSession()
				restaurants = session.query(Restaurant).all()

				res_list_items = []
				for restaurant in restaurants:
					edit_link = self.addr['res'] + '/' + str(restaurant.id) + '/edit'
					del_link = self.addr['res'] + '/' + str(restaurant.id) + '/delete'
					res_list_items.append(
						self.html['restaurant_item'] %
							(restaurant.name, edit_link, del_link))

				session.close()

				res_list_html = "".join(res_list_items)
				self.wfile.write(self.html['restaurant_page'] %
					(res_list_html, self.html['restaurant_add']))

				# except:
				# 	print 'Database connection error.'

				return

			elif(self.path_match(self.addr['res_add'])):
				self.send_response(200)
				self.send_header('Content-Type', 'text/html')
				self.end_headers()

				self.wfile.write(self.html['restaurant_add_page'])

				return

			elif(self.pattern['edit'].search(self.path)):

				try:
					res_id = self.pattern['edit_id'].search(self.path).group()
					session = self.DBSession()
					res = session.query(Restaurant).filter_by(id = res_id).one()
					session.close()

					if res is not None:
						self.send_response(200)
						self.send_header('Content-Type', 'text/html')
						self.end_headers()
						self.wfile.write(self.html['restaurant_edit_page'] %\
							(res.name, self.path))

				except:
					raise IOError

				return

			elif(self.pattern['del'].search(self.path)):
				try:
					res_id = self.pattern['del_id'].search(self.path).group()
					session = self.DBSession()
					res = session.query(Restaurant).filter_by(id = res_id).one()
					session.close()

					if res is not None:
						self.send_response(200)
						self.send_header('Content-Type', 'text/html')
						self.end_headers()
						self.wfile.write(self.html['restaurant_del_page'] % (res.name, self.path))

				except:
					raise IOError

				return

			else:
				raise IOError

		except IOError:
			self.send_response(404, "File Not Found on %s" % self.path)
			self.send_header('Content-Type', 'text/html')
			self.end_headers()

			self.wfile.write(self.html['not_found'])

	def do_POST(self):
		try:
			print self.path

			if (self.path_match(self.addr['hello'])) or\
				(self.path_match(self.addr['hola'])):
				self.send_response(302)
				self.send_header('location', self.addr['hello'])
				self.end_headers()

				ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
				if ctype == 'multipart/form-data':
					fields = cgi.parse_multipart(self.rfile, pdict)
					message = fields.get('message')

					global welcome_message
					welcome_message = message[0]
					print welcome_message

				return

			elif self.path_match(self.addr['res_add']):
				self.send_response(302)
				self.send_header('location', self.addr['res'])
				self.end_headers()

				ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
				if ctype == 'multipart/form-data':
					fields = cgi.parse_multipart(self.rfile, pdict)
					name = fields.get('name')[0]

					if len(name) != 0:
						newRes = Restaurant(name = name)
						session = self.DBSession()
						session.add(newRes)
						session.commit()
						session.close()

				return

			elif(self.pattern['edit'].search(self.path)):
				self.send_response(302)
				self.send_header('location', self.addr['res'])
				self.end_headers()

				ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
				if ctype == 'multipart/form-data':
					fields = cgi.parse_multipart(self.rfile, pdict)
					name = fields.get('name')[0]

				try:
					res_id = self.pattern['edit_id'].search(self.path).group()
					session = self.DBSession()
					res = session.query(Restaurant).filter_by(id = res_id).one()

					if res is not None:
						res.name = name
						session.add(res)
						session.commit()

					session.close()

				except:
					raise IOError

				return

			elif(self.pattern['del'].search(self.path)):
				self.send_response(302)
				self.send_header('location', self.addr['res'])
				self.end_headers()

				ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
				if ctype == 'multipart/form-data':
					fields = cgi.parse_multipart(self.rfile, pdict)
					confirm = fields.get('confirm')[0]

				if confirm == "Confirm":
					try:
						res_id = self.pattern['del_id'].search(self.path).group()
						session = self.DBSession()
						res = session.query(Restaurant).filter_by(id = res_id).one()

						if res is not None:
							session.delete(res)
							session.commit()

						session.close()

					except:
						raise IOError

				return

			else:
				raise IOError

		except IOError:
			self.send_response(404, "File Not Found on %s" % self.path)
			self.send_header('Content-Type', 'text/html')
			self.end_headers()

			self.wfile.write(self.html['not_found'])

def main():
	try:
		port = 8180
		server = HTTPServer(('', port), WebHandler)
		print "Server running on port %s" % port
		server.serve_forever()

	except KeyboardInterrupt:
		print "^C interruption triggerred. Server stopping..."
		server.socket.close()


if __name__ == "__main__":
	main()