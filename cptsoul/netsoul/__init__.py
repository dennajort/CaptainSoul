# -*- coding: utf-8 -*-

import logging
from time import time
from hashlib import md5
from collections import deque

from twisted.internet.protocol import connectionDone
from twisted.protocols.basic import LineOnlyReceiver

from cptsoul.common import CptCommon
from cptsoul.netsoul.tools import Rea, ReaList, NsUserCmdInfo, NsWhoResult, NsWhoEntry, urlEncode, urlDecode


class NsProtocol(LineOnlyReceiver, CptCommon):
    delimiter = '\n'

    def __init__(self, factory):
        self.factory = factory
        self.factory.setProtocol(self)
        self._responseQueue = deque()
        self._whoQueue = deque()
        self._realist = ReaList(
            Rea(r"^rep (?P<no>\d+) -- .*$", self._responseHook),
            Rea(r"^ping (?P<t>\d+)\s?$", self._pingHook),
            Rea(r"^salut (?P<num>\d+) (?P<md5_hash>[0-9a-fA-F]{32}) (?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
                r" (?P<port>\d{1,5}) (?P<timestamp>\d+)$", self._salutHook),
            Rea(r"^user_cmd (?P<no>\d+):\w+:\d+/\d+:(?P<login>.+)@(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
                r":.+:(?P<loc>.+):.+ \| (?P<cmd>.*)$", self._userCmdHook))
        self._cmd_realist = ReaList(
            Rea(r"^who (?P<no>\d+) (?P<login>.+) (?P<ip>[\d\.]{7,15}) \d+ \d+ \d+ \d+ .+ (?P<loc>.+)"
                r" .+ (?P<state>\w+)(:\d+)? (?P<res>.+)$", self._cmdWhoHook),
            Rea(r"^who rep 002 -- cmd end$", self._cmdWhoEndHook),
            Rea(r"^msg (?P<msg>.+) dst=(?P<dest>.*)$", self._cmdMsgHook),
            Rea(r"^state (?P<state>\w+?)(:\d+)?\s?$", self._cmdStateHook),
            Rea(r"^login\s?$", self._cmdLoginHook),
            Rea(r"^logout\s?$", self._cmdLogoutHook),
            Rea(r"^dotnetSoul_UserTyping null dst=.*$", self._cmdIsTypingHook),
            Rea(r"^dotnetSoul_UserCancelledTyping null dst=.*$", self._cmdCancelTypingHook),
            Rea(r"^file_ask (?P<data>.+) dst=.*$", self._cmdFileAskHook),
            Rea(r"^file_start (?P<data>.+) dst=.*$", self._cmdFileStartHook)
        )

    def lineReceived(self, line):
        logging.debug('Netsoul : <<   : "%s"' % line)
        self.factory.rawHook(line)
        if not self._realist.found_match(line):
            logging.warning('Netsoul : Unknown line : "%s"' % line)

    def connectionLost(self, reason=connectionDone):
        pass

    def connectionMade(self):
        self.factory.connectionMadeHook()

    def sendLine(self, line):
        super(NsProtocol, self).sendLine(str(line))
        logging.debug('Netsoul :   >> : "%s"' % line)
        self.factory.sendRawHook(line)

    # HOOKS

    def _userCmdHook(self, no, login, ip, loc, cmd):
        if not self._cmd_realist.found_match_cmd(cmd, NsUserCmdInfo(int(no), login, ip, loc)):
            logging.warning('Netsoul : Unknown cmd from %s@%s : "%s"' % (login, ip, cmd))

    def _responseHook(self, no):
        no = int(no)
        if self._responseQueue:
            logging.info('Netsoul : Got response %d' % no)
            self._responseQueue.popleft()(no)
        else:
            logging.warning('Netsoul : No response expected')

    def _pingHook(self, t):
        logging.info('Netsoul : Got ping %d' % int(t))
        self.sendLine('ping %s' % t)

    def _salutHook(self, num, md5_hash, ip, port, timestamp):
        logging.info('Netsoul : Got salut %s %s:%s' % (md5_hash, ip, port))
        self.info['hash'] = md5_hash
        self.info['host'] = ip
        self.info['port'] = port
        self.sendLine('auth_ag ext_user none none')
        self._responseQueue.append(self._responseSalutHook)

    # CMD HOOKS

    def _cmdWhoHook(self, info, no, login, ip, loc, state, res):
        if self._whoQueue:
            self._whoQueue[0].add(NsWhoEntry(no, login, ip, loc, state, res))
        else:
            logging.warning("Netsoul : No who expected")

    def _cmdWhoEndHook(self, info):
        if self._whoQueue:
            self.factory.cmdWhoHook(self._whoQueue.popleft())
        else:
            logging.warning("Netsoul : No who expected")

    def _cmdMsgHook(self, info, msg, dest):
        self.factory.cmdMsgHook(info, urlDecode(msg), dest.split(','))

    def _cmdLoginHook(self, info):
        self.factory.cmdLoginHook(info)

    def _cmdLogoutHook(self, info):
        self.factory.cmdLogoutHook(info)

    def _cmdStateHook(self, info, state):
        self.factory.cmdStateHook(info, state)

    def _cmdIsTypingHook(self, info):
        self.factory.cmdIsTypingHook(info)

    def _cmdCancelTypingHook(self, info):
        self.factory.cmdCancelTypingHook(info)

    def _cmdFileAskHook(self, info, data):
        name, size, desc, pas = urlDecode(data).split(' ', 4)
        self.factory.cmdFileAskHook(info, urlDecode(name), int(size), urlDecode(desc))

    def _cmdFileStartHook(self, info, data):
        name, ip, port = urlDecode(data).split(' ', 3)
        self.factory.cmdFileStartHook(info, urlDecode(name), urlDecode(ip), int(port))

    # RESPONSE HOOKS

    def _responseSalutHook(self, no):
        if no == 2:
            md5_hash = md5('%s-%s/%s%s' % (
                self.info['hash'], self.info['host'], self.info['port'], self.config['password'])).hexdigest()
            self.sendLine('ext_user_log %s %s %s %s' % (
                self.config['login'], md5_hash, urlEncode(self.config['location']), 'CaptainSoul'))
            self._responseQueue.append(self._responseLogHook)
        else:
            logging.warning('Netsoul : Salut response unknown %d' % no)

    def _responseLogHook(self, no):
        if no == 2:
            self.factory.loggedHook()
        elif no == 33:
            self.factory.loginFailedHook()
        elif no == 131:
            # permission denied
            self.factory.loginFailedHook()
        else:
            logging.warning('Netsoul : Log response unknown %d' % no)
            self.factory.loginFailedHook()

    # COMMANDS

    def sendState(self, state):
        if state:
            self.sendLine('state %s:%d' % (state, time()))

    def sendWatch(self, sendWho=True):
        self.sendLine('user_cmd watch_log_user {%s}' % ','.join(self.config['watchlist']))
        if sendWho:
            self.sendWho(self.config['watchlist'])

    def sendWho(self, logins):
        if logins:
            self._whoQueue.append(NsWhoResult(logins))
            self.sendLine('user_cmd who {%s}' % ','.join(logins))

    def sendExit(self):
        self.sendLine('exit')

    def sendCmdUser(self, cmd, data, dests):
        if cmd and data and dests:
            self.sendLine('user_cmd msg_user {%s} %s %s' % (','.join(dests), cmd, urlEncode(data)))

    def sendMsg(self, msg, dests):
        self.sendCmdUser('msg', msg, dests)

    def sendStartTyping(self, dests):
        self.sendCmdUser('dotnetSoul_UserTyping', 'null', dests)

    def sendCancelTyping(self, dests):
        self.sendCmdUser('dotnetSoul_UserCancelledTyping', 'null', dests)

    def sendFileAsk(self, name, size, desc, dests):
        self.sendCmdUser('file_ask', '%s %d %s passive' % (urlEncode(name), size, urlEncode(desc)), dests)

    def sendFileStart(self, name, ip, port, dests):
        self.sendCmdUser('file_start', '%s %s %d' % (urlEncode(name), ip, port), dests)
