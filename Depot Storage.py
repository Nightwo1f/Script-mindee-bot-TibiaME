################################################
#            Depot Storage script              #
################################################
# Store items from autoloot list.
# Keep this False if you want to store from the list below.
StoreFromAutoloot = True
StoreItemsList = [5217,5224,5220,5138,2566,2587]

# Move directly to switching spot as soon as storages are full.
MoveDirectlyToSwitch = True

# Play alarm when depot is full.
PlayAlarm = True

# Logout when depot is full.
LogoutFull = False

# Stop hunting if depot is full. (Character won't go to hunting grounds and will stay below depot.)
# False = character will continue hunting, but won't go to depot.
# If LogoutFull is enabled, this one is ignored.
StopHuntFull = False

# Ignore monsters when on route to depot.
IgnoreMonstersTo = True
# Ignore monsters when on route back to cave.
IgnoreMonstersBack = True
# Ignore monsters when on route to the switch spot.
IgnoreMonstersSwitch = True
# Ignore monsters when at hunting cave (Waypoints set: hunt).
# Useful when you just want to loot items.
IgnoreMonstersHunt = False

# Depot location (tile below depot).
DEPOT_SPOT = Location(31951, 31984, 7)
# Spot location at hunting grounds (used to switch waypoint sets).
SWITCH_SPOT = Location(31948, 31980, 8)

# Paths
# Make hunting path in set 0.
# Make to depot spot path in set 1.
# Make back to hunt switch spot path in set 2.
hunt = 0
to_depot = 1
back = 2

################################################
# Don't touch this if you want to live.
CheckedList = []

def onScriptActivation():
	CheckIgnoring()
	del CheckedList[:]
	script.SetVar('StopDepot', False)

def onScriptDeactivation():
	if script.IsInShop():
		script.SetVar('depotMode', 0)
		script.LeaveShop()

def onChangeLocation(x, y, z):
	xyz = Location(x,y,z)
	if xyz == DEPOT_SPOT:
		if script.GetWay() == to_depot and not script.GetVar('StopDepot'):
			if script.EnterShop():
				script.SetVar('depotMode', 1)
				script.StatusMessage('Entering depot.')
			else:
				script.Alarm('Can\'t find depot.')
	elif xyz == SWITCH_SPOT:
		if script.IsStorageFull() and not script.GetVar('StopDepot'):
			if script.GetWay() != to_depot:
				script.StatusMessage('Going to depot to store items...')
				ChangeWay(to_depot)
		elif script.GetWay() != hunt:
			script.StatusMessage('Hunting started!')
			ChangeWay(hunt)

def onReceiveDepotMenu(depot_name, depot_id, depot_type, slots):
	if not script.IsInShop(): # not in depot
		return
		
	if script.GetVar('depotMode') == 0:
		return

	script.SetVar('depot_id', depot_id)
	script.SetVar('depot_type', depot_type)

	script.RunEvent('DoStorage', 1000)

def onReceiveAddItemToBackpack(slot, itemId):
	if script.GetVar('depotMode') == 0:
		if not MoveDirectlyToSwitch:
			return
		
		if script.GetVar('StopDepot'):
			return

		if script.IsStorageFull():
			if script.GoToLocationEx(SWITCH_SPOT.x, SWITCH_SPOT.y, SWITCH_SPOT.z):
				script.IgnoreMonsters(IgnoreMonstersSwitch)
				script.StatusMessage('Storages are full.\nGoing to the switch spot.')
			else:
				script.StatusMessage('Storages are full.\nWarning! Will move by the waypoints at this time.')
	elif script.GetVar('depotMode') == 2:
		if script.GetFreeBackpackSlot() != 255: # there is room in backpack, try retrieving stuff from inventory, depotmail
			if CheckRetrieval(script.GetVar('depot_id'), script.GetVar('depot_type')):
				script.StatusMessage('Item retrieved to backpack: ' + str(itemId) + '\n Checking for more...')
				return
		
		script.StatusMessage('Returning to storage mode.')
		script.SetVar('depotMode', 1)
		script.RunEvent('DoStorage', 1000)

def onReceiveAddItemToDepot(slot, itemId):
	if not script.IsInShop():
		return

	if script.GetVar('depotMode') != 1:
		return

	script.StatusMessage('Item stored to depot: ' + str(itemId) + '\n Checking for more...')
	script.RunEvent('DoStorage', 1000)

def LeaveDepot():
	del CheckedList[:]
	script.SetVar('depotMode', 0)
	script.LeaveShop()

def DoRetrieve():
	if not script.IsInShop():
		return

	if script.GetVar('depotMode') != 2:
		return

	depot_id = script.GetVar('depot_id')
	depot_type = script.GetVar('depot_type')
	
	if script.GetFreeBackpackSlot() == 255:
		script.SetVar('depotMode', 1)
		script.RunEvent('DoStorage', 1000)
		return

	retrieveSlot = -1
	if depot_type == 0:
		retrieveSlot = GetSomethingForRetrieve(1)
	elif depot_type == 1:
		retrieveSlot = GetSomethingForRetrieve(2)

	if retrieveSlot == -1:
		script.SetVar('depotMode', 1)
		script.RunEvent('DoStorage', 1000)
		return

	if not script.RetrieveSlotToBackpack(retrieveSlot, depot_type):
		script.StatusMessage('Failed to retrieve slot: ' + str(retrieveSlot) + '\nTrying again...')
		script.RunEvent('DoRetrieve', 1000)
	else:
		script.StatusMessage('Retrieving slot: ' + str(retrieveSlot))

def CheckRetrieval(depot_id, depot_type):
	if GetSomethingForRetrieve(1) != -1:
		if depot_type != 0:
			script.SwitchDepotPage(depot_id + 1)
			script.StatusMessage('Not in inventory page: ' + str(depot_id) + '\nSwitching...')
		else:
			script.SetVar('depotMode', 2)
			script.RunEvent('DoRetrieve', 1000)
		return True

	if GetSomethingForRetrieve(2) != -1:
		if depot_type != 1:
			script.SwitchDepotPage(depot_id + 1)
			script.StatusMessage('Not in depotmail page: ' + str(depot_id) + '\nSwitching...')
		else:
			script.SetVar('depotMode', 2)
			script.RunEvent('DoRetrieve', 1000)
		return True

	return False

def DoStorage():
	if not script.IsInShop():
		return
		
	if script.GetVar('depotMode') != 1:
		return

	depot_id = script.GetVar('depot_id')
	depot_type = script.GetVar('depot_type')
	
	storeSlot = GetSomethingForStorage()
	if storeSlot == -1:
		if script.GetFreeBackpackSlot() != 255: # there is room in backpack, try retrieving stuff from inventory, depotmail
			if CheckRetrieval(depot_id, depot_type):
				del CheckedList[:]
				return

		script.StatusMessage('Nothing to store.\nLeaving depot...')
		ChangeWay(back)
		LeaveDepot()
		return
	
	if depot_type != 2:
		script.SwitchDepotPage(depot_id + 1)
		script.StatusMessage('Not in depot page: ' + str(depot_id) + '\nSwitching...')
		return

	if script.GetFreeDepotSlotCount() == 0:
		if not (depot_id in CheckedList):
			script.SwitchDepotPage(depot_id + 1)
			CheckedList.append(depot_id)
			script.StatusMessage('No slots in this page: ' + str(depot_id) + '\n Switching...')
		else:
			if PlayAlarm:
				script.Alarm('Depot is full!')
			if LogoutFull:
				script.Logout()
			else:
				if StopHuntFull:
					script.StatusMessage('Depot is full!\nScript now will stop...')
				else:
					ChangeWay(back)
					script.StatusMessage('Depot is full!\nWill stop going to depot.\nLeaving depot...')
			script.SetVar('StopDepot', True)
			LeaveDepot()
			return
		return

	if not script.StoreSlotInDepot(storeSlot):
		script.StatusMessage('Error storing!\nTrying again...')
		script.RunEvent('DoStorage', 1000)
	else:
		script.StatusMessage('Storing item from slot: ' + str(storeSlot) + ' (Depot: ' + str(depot_id) + ')')

def IsValidForStorage(item):
	if StoreFromAutoloot:
		return script.IsInLoot(item)
	
	return item in StoreItemsList

def GetSomethingForRetrieve(type):
	items = None
	if type == 1:
		items = script.GetInventoryItems()
	elif type == 2:
		items = script.GetDepotmailItems()

	if items == None:
		return -1
		
	size = len(items)

	for i in range(size):
		item = items[i]
		if IsValidForStorage(item):
			return i + 1
	return -1

def GetSomethingForStorage():
	items = script.GetBackpackItems()
	if items == None:
		return -1

	for i in range(9):
		item = items[i]
		if IsValidForStorage(item):
			return i + 1
	return -1

def CheckIgnoring():
	way = script.GetWay()

	if way == to_depot:
		script.IgnoreMonsters(IgnoreMonstersTo)
	elif way == back:
		script.IgnoreMonsters(IgnoreMonstersBack)
	else:
		script.IgnoreMonsters(IgnoreMonstersHunt)

def ChangeWay(way):
	script.SetWay(way, 2)
	CheckIgnoring()
