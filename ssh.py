version = (2, 0, 0)

# meta developer: @RUIS_VlP
# requires: paramiko

import asyncio
import os
import random
import string
from .. import loader, utils

import paramiko


class SSHConnection:
	
	def __init__(self, host, port, username, password=None, key_path=None):
		self.host = host
		self.port = port
		self.username = username
		self.password = password
		self.key_path = key_path
		self.client = None
		
	async def connect(self):
		loop = asyncio.get_event_loop()
		await loop.run_in_executor(None, self._connect_sync)
		
	def _connect_sync(self):
		self.client = paramiko.SSHClient()
		self.client.load_system_host_keys()
		self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		
		connect_kwargs = {
			'hostname': self.host,
			'port': self.port,
			'username': self.username
		}
		
		if self.key_path and self.key_path != "None":
			try:
				private_key = paramiko.RSAKey.from_private_key_file(self.key_path)
				connect_kwargs['pkey'] = private_key
			except:
				try:
					private_key = paramiko.Ed25519Key.from_private_key_file(self.key_path)
					connect_kwargs['pkey'] = private_key
				except:
					private_key = paramiko.ECDSAKey.from_private_key_file(self.key_path)
					connect_kwargs['pkey'] = private_key
		else:
			connect_kwargs['password'] = self.password
			
		self.client.connect(**connect_kwargs)
		
	async def upload_file(self, local_file, remote_file):
		loop = asyncio.get_event_loop()
		await loop.run_in_executor(None, self._upload_file_sync, local_file, remote_file)
		
	def _upload_file_sync(self, local_file, remote_file):
		sftp = self.client.open_sftp()
		
		remote_dir = os.path.dirname(remote_file)
		if remote_dir:
			self._create_remote_dir(sftp, remote_dir)
		
		sftp.put(local_file, remote_file)
		sftp.close()
		
	def _create_remote_dir(self, sftp, path):
		dirs = []
		while path and path != '/':
			try:
				sftp.stat(path)
				break
			except IOError:
				dirs.append(path)
				path = os.path.dirname(path)
		
		while dirs:
			dir_path = dirs.pop()
			try:
				sftp.mkdir(dir_path)
			except IOError:
				pass
	
	async def download_file(self, remote_file, local_file):
		loop = asyncio.get_event_loop()
		await loop.run_in_executor(None, self._download_file_sync, remote_file, local_file)
		
	def _download_file_sync(self, remote_file, local_file):
		sftp = self.client.open_sftp()
		sftp.get(remote_file, local_file)
		sftp.close()
		
	async def execute_command_stream(self, command, callback):
		loop = asyncio.get_event_loop()
		return await loop.run_in_executor(
			None, 
			self._execute_command_stream_sync, 
			command, 
			callback
		)
		
	def _execute_command_stream_sync(self, command, callback):
		stdin, stdout, stderr = self.client.exec_command(command, get_pty=True)
		
		channel = stdout.channel
		pid = channel.get_id()
		
		output_lines = []
		error_lines = []
		
		while not stdout.channel.exit_status_ready() or stdout.channel.recv_ready():
			if stdout.channel.recv_ready():
				line = stdout.readline()
				if line:
					output_lines.append(line)
					callback('stdout', line, pid)
					
		remaining = stdout.read().decode()
		if remaining:
			output_lines.append(remaining)
			callback('stdout', remaining, pid)
			
		error_output = stderr.read().decode()
		if error_output:
			error_lines.append(error_output)
			callback('stderr', error_output, pid)
			
		exit_code = stdout.channel.recv_exit_status()
		
		return exit_code, ''.join(output_lines), ''.join(error_lines), pid
		
	def close(self):
		if self.client:
			self.client.close()


@loader.tds
class SSHMod(loader.Module):
	"""Модуль для работы с SSH"""

	strings = {
		"name": "SSHMod",
		"cfg_host": "IP address or domain",
		"cfg_username": "SSH username",
		"cfg_password": "SSH password (leave None if using key)",
		"cfg_key": "Path to private SSH key (leave None if using password)",
		"cfg_port": "SSH port",
		"cfg_default_dir": "Default directory for saving files",
		"sftpsave_description": "<reply> [directory] - saves the file to the specified directory",
		"sftpsave_uploading": "<b>Starting upload....</b>",
		"sftpsave_success": "<b>File uploaded to SSH server, file location:</b> <code>{}</code>",
		"sftpsave_no_file": "<b>No files found in the message!</b>",
		"sftpsave_reply_required": "<b>The command must be a reply to a message!</b>",
		"sftpupload_description": "<file_path> - downloads file from SSH server",
		"sftpupload_no_path": "<b>No file path specified!</b>",
		"sftpupload_downloading": "<b>Downloading file from SSH server...</b>",
		"sftpupload_error": "<b>Error downloading file:</b> <code>{}</code>",
		"sterminal_description": "<command> - executes a command on the SSH server",
		"sterminal_no_command": "<b>No command specified!</b>",
		"sterminal_starting": "⌨️<b> System command</b>\n<pre><code class='language-bash'>{}</code></pre>\n<b>PID:</b> <code>{}</code>\n<b>Status:</b> Running...\n<b>📼 Output:</b>\n<pre><code class='language-stdout'>{}</code></pre>",
		"sterminal_output": "⌨️<b> System command</b>\n<pre><code class='language-bash'>{}</code></pre>\n<b>PID:</b> <code>{}</code>\n<b>Exit code:</b> <code>{}</code>\n<b>📼 Output:</b>\n<pre><code class='language-stdout'>{}</code></pre>",
		"sterminal_error": "⌨️<b> System command</b>\n<pre><code class='language-bash'>{}</code></pre>\n<b>PID:</b> <code>{}</code>\n<b>Exit code:</b> <code>{}</code>\n<b>🚫 Errors:</b>\n<pre><code class='language-stderr'>{}</code></pre>",
		"sterminal_output_and_error": "⌨️<b> System command</b>\n<pre><code class='language-bash'>{}</code></pre>\n<b>PID:</b> <code>{}</code>\n<b>Exit code:</b> <code>{}</code>\n<b>📼 Output:</b>\n<pre><code class='language-stdout'>{}</code></pre>\n<b>🚫 Errors:</b>\n<pre><code class='language-stderr'>{}</code></pre>",
		"sterminal_stopped": "⌨️<b> System command</b>\n<pre><code class='language-bash'>{}</code></pre>\n<b>PID:</b> <code>{}</code>\n<b>Status:</b> ⛔ Stopped by user\n<b>📼 Output:</b>\n<pre><code class='language-stdout'>{}</code></pre>",
		"addkey_description": "<key_content> - saves SSH private key to .ssh directory",
		"addkey_no_key": "<b>No key content provided!</b>",
		"addkey_success": "<b>Key saved successfully!</b>\n<b>Key file:</b> <code>{}</code>\n<b>Full path:</b> <code>{}</code>\n\nYou can now set it in config:\n<code>.fcfg SSHMod key_path {}</code>",
		"addkey_error": "<b>Error saving key:</b> <code>{}</code>",
		"config_not_set": "<b>Values are not set. Set them using the command:</b>\n<code>.config SSHMod</code>",
		"stop_button": "⛔ Stop",
	}

	strings_ru = {
		"name": "SSHMod",
		"cfg_host": "IP-адрес или домен",
		"cfg_username": "Имя пользователя SSH",
		"cfg_password": "Пароль SSH (оставьте None при использовании ключа)",
		"cfg_key": "Путь к закрытому SSH ключу (оставьте None при использовании пароля)",
		"cfg_port": "Порт SSH",
		"cfg_default_dir": "Директория по умолчанию для сохранения файлов",
		"sftpsave_description": "<reply> [директория] - сохраняет файл в указанную директорию",
		"sftpsave_uploading": "<b>Начинаю загрузку....</b>",
		"sftpsave_success": "<b>Файл загружен на SSH сервер, расположение файла:</b> <code>{}</code>",
		"sftpsave_no_file": "<b>В сообщении не найдены файлы!</b>",
		"sftpsave_reply_required": "<b>Команда должна быть ответом на сообщение!</b>",
		"sftpupload_description": "<путь_к_файлу> - скачивает файл с SSH сервера",
		"sftpupload_no_path": "<b>Не указан путь к файлу!</b>",
		"sftpupload_downloading": "<b>Скачиваю файл с SSH сервера...</b>",
		"sftpupload_error": "<b>Ошибка при скачивании файла:</b> <code>{}</code>",
		"sterminal_description": "<command> - выполняет команду на SSH сервере",
		"sterminal_no_command": "<b>Не указана команда для выполнения!</b>",
		"sterminal_starting": "⌨️<b> Системная команда</b>\n<pre><code class='language-bash'>{}</code></pre>\n<b>PID:</b> <code>{}</code>\n<b>Статус:</b> Выполняется...\n<b>📼 Вывод:</b>\n<pre><code class='language-stdout'>{}</code></pre>",
		"sterminal_output": "⌨️<b> Системная команда</b>\n<pre><code class='language-bash'>{}</code></pre>\n<b>PID:</b> <code>{}</code>\n<b>Код выхода:</b> <code>{}</code>\n<b>📼 Вывод:</b>\n<pre><code class='language-stdout'>{}</code></pre>",
		"sterminal_error": "⌨️<b> Системная команда</b>\n<pre><code class='language-bash'>{}</code></pre>\n<b>PID:</b> <code>{}</code>\n<b>Код выхода:</b> <code>{}</code>\n<b>🚫 Ошибки:</b>\n<pre><code class='language-stderr'>{}</code></pre>",
		"sterminal_output_and_error": "⌨️<b> Системная команда</b>\n<pre><code class='language-bash'>{}</code></pre>\n<b>PID:</b> <code>{}</code>\n<b>Код выхода:</b> <code>{}</code>\n<b>📼 Вывод:</b>\n<pre><code class='language-stdout'>{}</code></pre>\n<b>🚫 Ошибки:</b>\n<pre><code class='language-stderr'>{}</code></pre>",
		"sterminal_stopped": "⌨️<b> Системная команда</b>\n<pre><code class='language-bash'>{}</code></pre>\n<b>PID:</b> <code>{}</code>\n<b>Статус:</b> ⛔ Остановлено пользователем\n<b>📼 Вывод:</b>\n<pre><code class='language-stdout'>{}</code></pre>",
		"addkey_description": "<содержимое_ключа> - сохраняет SSH ключ в директорию .ssh",
		"addkey_no_key": "<b>Не указано содержимое ключа!</b>",
		"addkey_success": "<b>Ключ успешно сохранён!</b>\n<b>Имя файла:</b> <code>{}</code>\n<b>Полный путь:</b> <code>{}</code>\n\nДля применения напишите:\n<code>.fcfg SSHMod key_path {}</code>",
		"addkey_error": "<b>Ошибка при сохранении ключа:</b> <code>{}</code>",
		"config_not_set": "<b>Значения не указаны. Укажите их через команду:</b>\n<code>.config SSHMod</code>",
		"stop_button": "⛔ Остановить",
	}

	def __init__(self):
		self.config = loader.ModuleConfig(
			loader.ConfigValue(
				"host",
				"None",
				lambda: self.strings["cfg_host"],
				validator=loader.validators.String(),
			),
			loader.ConfigValue(
				"username",
				"None",
				lambda: self.strings["cfg_username"],
				validator=loader.validators.String(),
			),
			loader.ConfigValue(
				"password",
				"None",
				lambda: self.strings["cfg_password"],
				validator=loader.validators.Hidden(),
			),
			loader.ConfigValue(
				"key_path",
				"None",
				lambda: self.strings["cfg_key"],
				validator=loader.validators.String(),
			),
			loader.ConfigValue(
				"Port",
				22,
				lambda: self.strings["cfg_port"],
				validator=loader.validators.Integer(),
			),
			loader.ConfigValue(
				"default_directory",
				"sshmod",
				lambda: self.strings["cfg_default_dir"],
				validator=loader.validators.String(),
			),
		)
		self.active_tasks = {}

	@loader.command()
	async def sftpsave(self, message):
		"""<reply> [dir] - сохраняет указанных файл на сервер"""
		host = self.config["host"]
		username = self.config["username"]
		password = self.config["password"]
		key_path = self.config["key_path"]
		port = self.config["Port"]
		
		if host == "None" or username == "None" or (password == "None" and key_path == "None"):
			await utils.answer(message, self.strings["config_not_set"])
			return
			
		reply = await message.get_reply_message()
		if not reply:
			await utils.answer(message, self.strings["sftpsave_reply_required"])
			return
			
		if not reply.media:
			await utils.answer(message, self.strings["sftpsave_no_file"])
			return
		args = utils.get_args_raw(message)
		remote_dir = args if args else self.config["default_directory"]
		
		await utils.answer(message, self.strings["sftpsave_uploading"])
		
		file_path = await message.client.download_media(reply.media)
		file_name = os.path.basename(file_path)
		sftp_path = f"{remote_dir}/{file_name}"
		
		conn = SSHConnection(host, port, username, password, key_path)
		await conn.connect()
		await conn.upload_file(file_path, sftp_path)
		conn.close()
		
		os.remove(file_path)
		
		await utils.answer(
			message,
			self.strings["sftpsave_success"].format(sftp_path),
		)

	@loader.command()
	async def sftpdownload(self, message):
		"""<path> - скачивает указанных файл с сервера"""
		host = self.config["host"]
		username = self.config["username"]
		password = self.config["password"]
		key_path = self.config["key_path"]
		port = self.config["Port"]
		
		if host == "None" or username == "None" or (password == "None" and key_path == "None"):
			await utils.answer(message, self.strings["config_not_set"])
			return
			
		remote_path = utils.get_args_raw(message)
		if not remote_path:
			await utils.answer(message, self.strings["sftpupload_no_path"])
			return
			
		await utils.answer(message, self.strings["sftpupload_downloading"])
		
		local_file = f"/tmp/sftp_download_{random.randint(1000, 9999)}_{os.path.basename(remote_path)}"
		
		try:
			conn = SSHConnection(host, port, username, password, key_path)
			await conn.connect()
			await conn.download_file(remote_path, local_file)
			conn.close()
			
			await utils.answer_file(
				message,
				local_file,
				f"📥 File from SSH server: <code>{remote_path}</code>"
			)
			
			if os.path.exists(local_file):
				os.remove(local_file)
				
		except Exception as e:
			await utils.answer(message, self.strings["sftpupload_error"].format(str(e)))
			if os.path.exists(local_file):
				os.remove(local_file)

	@loader.command()
	async def addkey(self, message):
		"""<ключ> - сохраняет указанный ssh ключ"""
		key_content = utils.get_args_raw(message)
		
		if not key_content:
			await utils.answer(message, self.strings["addkey_no_key"])
			return
			
		try:
			ssh_dir = os.path.expanduser("~/.ssh")
			os.makedirs(ssh_dir, exist_ok=True)
			
			random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
			key_filename = f"ssh_key_{random_name}"
			key_path = os.path.join(ssh_dir, key_filename)
			
			with open(key_path, 'w') as f:
				f.write(key_content)
			
			os.chmod(key_path, 0o600)
			
			await utils.answer(
				message,
				self.strings["addkey_success"].format(key_filename, key_path, key_path)
			)
			
		except Exception as e:
			await utils.answer(message, self.strings["addkey_error"].format(str(e)))

	@loader.command(alias="ssh")
	async def sterminal(self, message):
		"""<команда> - выполняет команду на ssh сервере"""
		host = self.config["host"]
		username = self.config["username"]
		password = self.config["password"]
		key_path = self.config["key_path"]
		port = self.config["Port"]
		
		if host == "None" or username == "None" or (password == "None" and key_path == "None"):
			await utils.answer(message, self.strings["config_not_set"])
			return
			
		command = utils.get_args_raw(message)
		if not command:
			await utils.answer(message, self.strings["sterminal_no_command"])
			return

		conn = SSHConnection(host, port, username, password, key_path)
		await conn.connect()
		
		output_buffer = []
		error_buffer = []
		current_pid = None
		stop_flag = False
		
		def stream_callback(stream_type, data, pid):
			nonlocal current_pid
			if current_pid is None:
				current_pid = pid
			if stream_type == 'stdout':
				output_buffer.append(data)
			else:
				error_buffer.append(data)
		
		stop_button = {
			"text": self.strings["stop_button"],
			"callback": self._stop_callback,
			"args": (message.chat_id, message.id),
		}
		
		task_id = f"{message.chat_id}_{message.id}"
		self.active_tasks[task_id] = {'stop': False, 'conn': conn}
		
		msg = await utils.answer(
			message, 
			self.strings["sterminal_starting"].format(command, "...", ""),
			reply_markup=[[stop_button]]
		)
		
		async def execute_task():
			try:
				exit_code, output, error, pid = await conn.execute_command_stream(
					command, 
					stream_callback
				)
				
				if self.active_tasks.get(task_id, {}).get('stop'):
					current_output = ''.join(output_buffer)
					await utils.answer(
						msg,
						self.strings["sterminal_stopped"].format(
							command, 
							pid if pid else "N/A",
							current_output if current_output else "No output"
						)
					)
				else:
					if output and not error:
						response = self.strings["sterminal_output"].format(command, pid, exit_code, output)
					elif error and not output:
						response = self.strings["sterminal_error"].format(command, pid, exit_code, error)
					elif output and error:
						response = self.strings["sterminal_output_and_error"].format(command, pid, exit_code, output, error)
					else:
						response = f"⌨️<b> System command</b>\n<pre><code class='language-bash'>{command}</code></pre>\n<b>PID:</b> <code>{pid}</code>\n<b>Exit code:</b> <code>{exit_code}</code>"
					
					await utils.answer(msg, response)
					
			except Exception as e:
				await utils.answer(msg, f"<b>Error:</b> {str(e)}")
			finally:
				conn.close()
				if task_id in self.active_tasks:
					del self.active_tasks[task_id]
		
		asyncio.create_task(execute_task())
		
		for _ in range(60): 
			await asyncio.sleep(2)
			
			if task_id not in self.active_tasks:
				break
				
			if self.active_tasks[task_id].get('stop'):
				break
				
			current_output = ''.join(output_buffer[-20:]) 
			if current_output:
				await msg.edit(
					self.strings["sterminal_starting"].format(
						command, 
						current_pid if current_pid else "...", 
						current_output[-1500:]  # Ограничение длины
					),
					reply_markup=[[stop_button]]
				)

	async def _stop_callback(self, call, chat_id, msg_id):
		"""Callback для кнопки остановки"""
		task_id = f"{chat_id}_{msg_id}"
		if task_id in self.active_tasks:
			self.active_tasks[task_id]['stop'] = True
			try:
				self.active_tasks[task_id]['conn'].close()
			except:
				pass
		await call.answer("Stopping...")