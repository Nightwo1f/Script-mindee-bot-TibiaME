############################################################
# By Budy w23 - @hazael
# ----------------------------------------------------------
# Script industrial de Hunt + Sell + Depot
# Especialista em ambos os modos
#
# ===================== COMANDOS PM ========================
# !base        → Vai para base
# !hunt        → Retoma hunt
# !mode sell   → Modo venda
# !mode depot  → Modo depot
#
############################################################


# ====================== MODOS ==============================

MODE_HUNT_SELL  = 1
MODE_HUNT_DEPOT = 2

ScriptStartMode = MODE_HUNT_SELL


# ====================== WAYPOINTS =========================

hunt       = 0
to_shop    = 1
back_shop  = 2
base       = 3
to_hunt    = 4
to_depot   = 5
back_depot = 6

# ====================== LOCAIS ============================

spot       = Location(31881, 32078, 12)
shop       = Location(31958, 31998, 7)
DEPOT_SPOT = Location(31951, 31984, 7)


# ====================== PLAYERS ===========================

CommandIssuers = ('player1', 'player2')


# ====================== ITENS =============================

SellItemsList = [3031, 3035]
DepotItemsList = [5217, 5224, 5220, 5138, 2566, 2587]

DropUnwantedItems = True
DropUnwantedItemsList = ('Hell crystal', 'Syorta ore')

# ================ NAO MEXA DAQUI EM DIANTE =============== #
# ====================== TIMERS ============================

SHOP_TIMEOUT     = 45
DEPOT_TIMEOUT    = 60
STUCK_TIMEOUT    = 12
COMMAND_DELAY    = 0.7


# ====================== ESTADOS ===========================

force_base = False
force_hunt = False

shopMode  = 0    # 0 idle | 1 selling | 2 leaving
depotMode = 0    # 0 idle | 1 storing | 2 changing_page | 3 leaving

checkedDepotPages = set()
currentDepotPage  = 1

last_action_time  = 0
last_command_time = 0
last_pos = None
last_move_time = 0

dropQueue = {}

script.SetVar('scriptMode', ScriptStartMode)


# ====================== UTIL ==============================

def now():
	return script.GetCurrentTime()

def UpdateAction():
	global last_action_time
	last_action_time = now()

def CanSendCommand():
	global last_command_time
	if now() - last_command_time < COMMAND_DELAY:
		return False
	last_command_time = now()
	return True


def ChangeWay(way):
	if not CanSendCommand():
		return
	script.SetWay(way, 2)
	UpdateAction()


# ====================== LOOT ==============================

def ShouldLootItem(itemId):
	mode = script.GetVar('scriptMode')
	if mode == MODE_HUNT_SELL:
		return itemId in SellItemsList
	if mode == MODE_HUNT_DEPOT:
		return itemId in DepotItemsList
	return False


# ====================== SHOP ==============================

def StartShop():
	global shopMode
	shopMode = 1
	UpdateAction()
	script.EnterShop()

def ProcessShop():
	global shopMode
	if shopMode == 1:
		for item in SellItemsList:
			script.SellItem(item)
		shopMode = 2
		UpdateAction()

def EndShop():
	global shopMode
	shopMode = 0
	script.LeaveShop()
	ChangeWay(back)


# ====================== DEPOT =============================

def StartDepot():
	global depotMode, currentDepotPage, checkedDepotPages
	depotMode = 1
	currentDepotPage = 1
	checkedDepotPages.clear()
	UpdateAction()
	script.EnterShop()

def ProcessDepot():
	global depotMode, currentDepotPage

	if depotMode == 1:
		for item in DepotItemsList:
			script.DepositItem(item)
		depotMode = 3
		UpdateAction()

def EndDepot():
	global depotMode
	depotMode = 0
	script.LeaveShop()
	ChangeWay(back)


# ====================== EVENTOS ===========================

def onScriptActivation():
	script.PZChecksForDrop(False)
	UpdateAction()
	script.StatusMessage('Unificado Shop+Depot ativo')


def onTick():
	global last_pos, last_move_time

	# WATCHDOG SHOP
	if script.IsInShop():
		if shopMode and now() - last_action_time > SHOP_TIMEOUT:
			script.StatusMessage('Shop timeout')
			EndShop()
		if depotMode and now() - last_action_time > DEPOT_TIMEOUT:
			script.StatusMessage('Depot timeout')
			EndDepot()

	# STUCK CHECK
	pos = script.GetPlayerPosition()
	if pos == last_pos:
		if now() - last_move_time > STUCK_TIMEOUT:
			ChangeWay(script.GetWay())
			last_move_time = now()
	else:
		last_pos = pos
		last_move_time = now()


def onReceiveMessagePrivate(name, message):
	global force_base, force_hunt

	if name not in CommandIssuers:
		return
	if not CanSendCommand():
		return

	cmd = message.lower().strip()

	if cmd == '!base':
		force_base = True
		script.GoToLocationEx(spot.x, spot.y, spot.z)
		return

	if cmd == '!hunt':
		force_hunt = True
		ChangeWay(to_hunt)
		return

	if cmd == '!mode sell':
		script.SetVar('scriptMode', MODE_HUNT_SELL)
		return

	if cmd == '!mode depot':
		script.SetVar('scriptMode', MODE_HUNT_DEPOT)
		return


def onReceiveItemDescriptionEx(itemId, name, slot):
	UpdateAction()

	if DropUnwantedItems and name in DropUnwantedItemsList:
		if script.DropItem(slot, 1) != 'ok':
			dropQueue[slot] = itemId
		script.IgnoreNextItem(itemId)
		return

	if not ShouldLootItem(itemId):
		script.IgnoreNextItem(itemId)
		return

	if script.IsStorageFull():
		script.GoToLocationEx(spot.x, spot.y, spot.z)


def onOpenContainer(containerId, name):
	if name not in ('Depot', 'Inbox', 'Store Inbox'):
		script.CloseContainer(containerId)


def onChangeLocation(x, y, z):
	UpdateAction()
	pos = Location(x,y,z)

	# ===== SPOT =====
	if pos == spot:

		if force_base:
			force_base = False
			ChangeWay(base)
			return

		if force_hunt:
			force_hunt = False
			ChangeWay(hunt)
			return

		if script.GetVar('scriptMode') == MODE_HUNT_DEPOT:
			if script.IsStorageFull():
				ChangeWay(to_depot)
			else:
				ChangeWay(hunt)
			return

		if script.IsStorageFull():
			ChangeWay(to_shop)
		else:
			ChangeWay(hunt)
		return

	# ===== SHOP =====
	if pos == shop and script.GetWay() == to_shop:
		StartShop()
		return

	# ===== DEPOT =====
	if pos == DEPOT_SPOT and script.GetWay() == to_depot:
		StartDepot()
		return


def onLeaveShop():
	UpdateAction()

	if shopMode:
		EndShop()

	if depotMode:
		EndDepot()
