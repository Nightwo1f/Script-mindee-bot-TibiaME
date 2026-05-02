# =============================================================================
# Nome do personagem que poderá controlar através de comandos no privado
allowedNames = "Logout"

#Comandos
# Logout = off
# Until HH:MM = off in time
# Base = go to base city
# Hunt = go to hunt
# Matar = Iniciar Caça

# =============================================================================

# Ignore monstros quando for para o shop.
IgnoreMonstersTo = True
# Ignore monstros quando estiver voltando para a hunt.
IgnoreMonstersBack = True
# Ignore monsters quando estiver na rota do spot.
IgnoreMonstersSwitch = True
# Ignore monstros na cave de hunt (Waypoints set: hunt).
# Útil quando quiser apenas pegar os itens no chão para vender.
IgnoreMonstersHunt = False

# Mover diretamente para a spot quando inventario estiver full. (Se o mapa da area estiver aberto)
MoveToSpotDirectly = True

# Descarte itens indesejados.
DropUnwantedItems = True

# Nomes dos itens que deve ser descartados:
DropUnwantedItemsList = (
	'Hell crystal',
	'Chili stick',
	'Your mom',
	'Bolkar\'s dildo'
)

# Tipo de venda: 
# 1 - Vende os itens um por um.
# 2 - vende tudo de uma vez.
# 3 - Vende um por um da backpack e todos do depotmail, inventario.
SellType = 3

# Variables
spot = Location(31982, 31915, 9) # Spot where path changes to hunt or shop. 'Shop' path starts from it and 'Back' ends in it.
shop = Location(31954, 31985, 7) # Spot near shop, player enters shop from it
ShopName = "Sam's Armoury" # Change to your shop name which you will be using
# For Scrapyard set to 1. For other shops set to 2.
SellOptionId = 2

# Paths
# Fazer o caminho de hunt no =  0.
# Fazer o caminho para o shop no =  1.
# Fazer a volta do shop no = 2.
hunt = 0
to_shop = 1
back = 2

# Don't touch these or I will cut your fingers!
ignore_menu = False
last_time_shop = 0

queue = {}

def onTick():
	global last_time_shop

	if not script.IsInShop():
		last_time_shop = 0
		return

	if last_time_shop > 0:
		cur_time = script.GetCurrentTime()
		if (cur_time - last_time_shop) > 60:
			last_time_shop = 0
			script.StatusMessage('Was stuck...')
			script.LeaveShopEx()
			
def onScriptActivation():
	global last_time_shop
	CheckIgnoring(script.GetWay())
	last_time_shop = 0
	script.EnableTickEvent(10000)
	script.PZChecksForDrop(False) # allow dropping items in protection zone
	script.PauseStorage(False)
	
def onScriptDeactivation():
	script.PauseStorage(False)
	if script.IsInShop():
		script.LeaveShop()

def onReceiveEnteredMenu(shopPacket, menuId, title):
	global ignore_menu, last_time_shop
	
	if title == ShopName:
		ignore_menu = False
		script.SetVar('checkedBackpack', False)
		script.SetVar('checkedInv', False)
		script.SetVar('checkedDep', False)

		last_time_shop = script.GetCurrentTime()
		script.StatusMessage('Shop: ' + title)
		if shopPacket:
			script.ChooseShopOption(menuId, SellOptionId) # Sell
	elif title == 'Sell':
		ignore_menu = False
		script.SetVar('lastMenuId', menuId)
		last_time_shop = script.GetCurrentTime()
		if script.GetWay() != back:
			ChangeWay(back)
		script.StatusMessage('Selling items...')
	elif title == 'Review Sell':
		ignore_menu = True
		last_time_shop = script.GetCurrentTime()
		script.ChooseShopOption(menuId, 1)
	else:
		ignore_menu = True

def onReceiveMenuRowsEx(rows):
	global last_time_shop

	if ignore_menu:
		return

	if SellType == 2:
		last_time_shop = script.GetCurrentTime()

		menuId = script.GetVar('lastMenuId')

		if not script.GetVar('checkedBackpack'):
			script.ChooseMenuOption(menuId, 1, 0)
			script.SetVar('checkedBackpack', True)
			return
		if not script.GetVar('checkedInv'):
			script.ChooseMenuOption(menuId, 1, 25600)
			script.SetVar('checkedInv', True)
			return
		if not script.GetVar('checkedDep'):
			script.ChooseMenuOption(menuId, 1, 25856)
			script.SetVar('checkedDep', True)
			return

		script.StatusMessage('Done.')
		script.LeaveShop()
	else:
		found = False

		for row in rows:
			list = row.split()
			menuId = int(list[0])
			rowId = int(list[1])
			title = list[2]
			looktype = int(list[3])
			isAct = int(list[-1])

			if SellType == 3 and isAct == 1 and ('Inventory' in title or 'Depotmail' in title):
				script.ChooseMenuOption(menuId, 1, rowId) # Sell item
				last_time_shop = script.GetCurrentTime()
				found = True
				break
			else:
				if script.IsInLoot(looktype):
					script.ChooseMenuOption(menuId, 1, rowId) # Sell item
					last_time_shop = script.GetCurrentTime()
					found = True
					break # break to avoid flood
		if not found:
			script.StatusMessage('Done.')
			script.LeaveShop() # didn't find items to sell.

def onReceiveMenuText(menuId, title, text):
	if title != 'Review Sell' and 'No entry in the list' in text:
		script.StatusMessage('Done.')
		script.LeaveShop()

def initResume():
	if len(queue) == 0:
		script.RunEvent('resumeStorage', 2000)
		
def resumeStorage(): # executed by RunEvent
	script.PauseStorage(False)

def onReceiveAddItemToBackpack(slot, itemId):
	if not DropUnwantedItems:
		return

	script.PauseStorage(True)

def onDroppedItem(slot):
	initResume()
	
def onReceiveItemDescriptionEx(itemId, name, slot):
	if DropUnwantedItems and name in DropUnwantedItemsList:
		if script.DropItem(slot, 1) == 'no_room':
			script.StatusMessage('No room! Adding to queue.')
			queue[slot] = itemId # add item to queue and drop it later
		else:
			script.StatusMessage('Dropping: ' + name)
			script.IgnoreNextItem(itemId)
	else: # item not in drop list, trying to resume storage
		if MoveToSpotDirectly and script.IsStorageFull():
			if script.GoToLocationEx(spot.x, spot.y, spot.z):
				script.IgnoreMonsters(IgnoreMonstersSwitch)
				script.StatusMessage('Storages are full.\nGoing to the spot.')
			else:
				script.StatusMessage('Storages are full.\nWarning! Will move by the waypoints at this time.')
		initResume()

def onChangeLocation(x, y, z):
	checkDropQueue(x, y, z)
	initResume()

	xyz = Location(x, y, z)
	if xyz == spot:
		if script.IsStorageFull():
			if script.GetWay() != to_shop:
				script.StatusMessage('Going to shop to sell items...')
				ChangeWay(to_shop)
		else:
			if script.GetWay() != hunt:
				script.StatusMessage('Hunt started!')
				ChangeWay(hunt)
	elif xyz == shop:
		if script.GetWay() == to_shop:
			if script.EnterShop():
				script.StatusMessage('Entering shop.')
			else:
				script.Alarm('Can\'t find the shop.')

def checkDropQueue(x, y, z):
	if not DropUnwantedItems:
		return

	if script.IsLocationFree(x, y, z):
		if len(queue) > 0: # there are items in queue, try to drop them
			for slot, itemId in queue.items():
				if script.GetItemInSlot(slot) == itemId:
					if script.DropItem(slot, 0) == 'ok':
						script.IgnoreNextItem(itemId)
						script.StatusMessage('Dropping item from queue.')
						queue.pop(slot) # Deletes item from queue
						break
				else:
					script.StatusMessage('Deleted item from queue.')
					queue.pop(slot) # Deletes item from queue, because it's not in slot.

def CheckIgnoring(way):
	if way == to_shop:
		script.IgnoreMonsters(IgnoreMonstersTo)
	elif way == back:
		script.IgnoreMonsters(IgnoreMonstersBack)
	else:
		script.IgnoreMonsters(IgnoreMonstersHunt)

def ChangeWay(way):
	script.SetWay(way, 2)
	CheckIgnoring(way)

# =============================================================================
# Funções para controle via mensagem privada

def onReceivePrivateMessage(name, text):
    if (name not in allowedNames):
        return

    elif ("Logout" in text):
        script.Logout()

    elif ("Until" in text):
        time = text.split()[-1]
        script.LogoutUntil(time)

    elif ("Base" in text):
        if script.GetWay() != to_base:
            script.StatusMessage('Go to base...')
            ChangeWay(to_base)
			return

    elif ("Hunt" in text):
        if script.GetWay() != to_hunt:
            script.StatusMessage('Back to hunt...')
            ChangeWay(to_hunt)
			return

    elif ("Matar" in text):
        if script.GetWay() != hunt:
            script.StatusMessage('Hunting')
            ChangeWay(hunt)
			return

            
# =============================================================================
