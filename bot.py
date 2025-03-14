import random
from turtle import end_fill
import db
import requests
import json
import re
import yaml

trans_list = eval(open('attr_trans.txt', encoding='utf-8').read())


def trans_attr(attr):
    if attr in trans_list:
        return trans_list[attr]
    return attr


def get_bind(update):
    uid = update.effective_user.id
    binds = db.get('bind')
    for pc_name, _uid in binds.items():
        if uid == _uid:
            return pc_name
    return None


class TGBot:
    def __init__(self) -> None:
        self.cmd_list = {
            'kp', 'reset',
            'rd', 'ra', 'sc',
            'add_pc', 'rm_pc', 'show_pc', 'set',
            'bind', 'unbind',
            'load_mod', 'tell', 'intro', 'battle',
        }

    def call(self, update, cmd):
        return getattr(self, f'{cmd[0]}')(update, cmd[1:])

    def load_mod(self, update, cmd):
        if update.effective_user.id != db.get('kp'):
            return "You are not KP!"
        fp = f'mod_{cmd[0].strip()}.yml'
        cont = yaml.safe_load(open(fp, encoding='utf-8').read())
        db.set('mod', cont)
        return "Mod loaded!"

    def tell(self, update, cmd):
        if update.effective_user.id != db.get('kp'):
            return "You are not KP!"
        mod = db.get('mod')
        return f'KP: {mod["story"][cmd[0]]}'

    def intro(self, update, cmd):
        if update.effective_user.id != db.get('kp'):
            return "You are not KP!"
        mod = db.get('mod')
        return f'KP: {mod["npc"][cmd[0]]}'

    def battle(self, update, cmd):
        if update.effective_user.id != db.get('kp'):
            return "You are not KP!"
        pcs = db.get('pc')
        eners = db.get('mod')['enermy']
        a = []
        for i in cmd:
            if i in pcs:
                a.append((i, pcs[i]['敏捷']))
            else:
                a.append((i, eners[i]['dex']))
        a.sort(key=lambda x: -x[1])
        a = ', '.join([i[0] for i in a])
        return f"Battle start, order: {a}"

    def rd(self, update, cmd):
        res = f'{update.effective_user.username} diced '
        for r in cmd:
            r = int(r)
            if r <= 1:
                raise Exception('Wrong boarder.')
            n = random.randint(1, r)
            res += f'{n} / {r} '
        return res

    def kp(self, update, cmd):
        if len(cmd) and cmd[0] == 'rm':
            db.set('kp', None)
            return "KP removed."
        now = db.get('kp')
        if now is None:
            db.set('kp', update.effective_user.id)
            return f"{update.effective_user.username} has been the KP."
        else:
            return f"Already has KP."

    def reset(self, update, cmd):
        if update.effective_user.username != 'vieyos':
            return "No access!"
        db.reset()
        return "ALL DATA RESETED."

    def show_pc(self, update, cmd):
        pc = db.get('pc')
        res = ''
        if not len(cmd):
            res += f'#{len(list(pc.keys()))} PC\n'
            i = 1
            for k, v in pc.items():
                res += f'{i}. {k}: {v["sex"]}, {v["age"]}\n'
                i += 1
        else:
            now = pc[cmd[0]]
            res = cmd[0] + '\n'
            for k, v in now.items():
                res += f'{k}: {v}\t'
        if not res:
            return "Fail to find PC."
        return res

    def rm_pc(self, update, cmd):
        pc = db.get('pc')
        if cmd[0] in pc:
            del pc[cmd[0]]
            db.set('pc', pc)
            return "PC removed."
        else:
            return "Fail to find PC."

    def set(self, update, cmd):
        pcs = db.get('pc')
        pc = cmd[0]
        if pc not in pcs:
            return "Fail to find PC."
        attr = trans_attr(cmd[1])
        v = cmd[2]
        if v.startswith(('+', '-')):
            pcs[pc][attr] += eval(v)
        else:
            pcs[pc][attr] = int(v)
        db.set('pc', pcs)
        return "Attribute updated."

    def add_pc(self, update, cmd):
        if cmd[0] == 'maoye':
            url = 'https://maoyetrpg.com/api/rolecard/share?&name=rolecard'
            r = requests.post(url, data=json.dumps({'chartid': cmd[1]}))
            r = json.loads(r.content)['data'][0]
            res = {
                'hp': int(r['hp']['total']),
                'mp': int(r['mp']['total']),
                'name': r['name']['chartname'],
                'age': int(r['name']['ages']),
                'sex': r['name']['sex'],
                'san': int(r['san']['have']),
            }
            p = r['touniang'].strip('.st').strip()
            a = re.findall(r'[0-9]+', p)
            b = re.split(r'[0-9]+', p)
            b = [i if '/' not in i else i.split('/')[0] for i in b]
            for k, v in zip(b, a):
                res[k] = int(v)
            pc = db.get('pc')
            pc[res['name']] = res
            db.set('pc', pc)
            return f"PC {res['name']} is uploaded from maoye."
        else:
            return "Unkown"

    def unbind(self, update, cmd):
        uid = update.effective_user.id
        binds = db.get('bind')
        _del = None
        for _name, _uid in binds.items():
            if _uid == uid:
                _del = _name
                break
        if _del is not None:
            del binds[_del]
        db.set('bind', binds)
        return "Unbind successfully."

    def bind(self, update, cmd):
        self.unbind(update, cmd)
        uid = update.effective_user.id
        binds = db.get('bind')
        pcs = db.get('pc')
        pc_name = cmd[0]
        if pc_name not in pcs:
            return "Fail to find PC."
        if pc_name not in binds:
            binds[pc_name] = uid
            db.set('bind', binds)
            return "Bind successfully."
        else:
            if binds[pc_name] == uid:
                return "Already bind to you!"
            else:
                return "Already bind to other pl!"

    def sc(self, update, cmd):
        pc = get_bind(update)
        if pc is None:
            return "Fail to find your PC."
        pcs = db.get('pc')
        n = random.randint(1, 100)
        b = pcs[pc]['san']
        if n <= b:
            return f'{pc} san check {n} / {b}, 成功！'
        v = cmd[0]
        res = 0
        if '+' in v:
            v = v.split('+')
            res = int(v[0])
            v = v[1]
        x, y = v.split('d')
        z = [random.randint(1, int(y)) for _ in range(int(x))]
        res += sum(z)
        ret = f'{pc} san check {n} / {b}, 失败！掉san：{res}'
        pcs[pc]['san'] -= res
        db.set('pc', pcs)
        return ret

    def ra(self, update, cmd):
        binds = db.get('bind')
        pcs = db.get('pc')
        pc_name = pc = None
        for _name, uid in binds.items():
            if uid == update.effective_user.id:
                pc_name = _name
                pc = pcs[_name]
                break
        if pc is None:
            return "Fail to find your PC."
        n = random.randint(1, 100)
        attr = trans_attr(cmd[0])
        b = int(pc[attr])
        if n < 3:
            r = '竟然是大成功耶！'
        elif n <= b / 5:
            r = '极难成功！'
        elif n <= b / 2:
            r = '困难成功！'
        elif n <= b:
            r = '成功！'
        elif n >= 96:
            r = '哇哦，大失败！'
        else:
            r = '失败咧！'
        return f'{pc_name} {attr} diced {n} / {b}, {r}'
