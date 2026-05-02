# Variables
spot = Location(31962, 31986, 7) # Spot where path changes to hunt or shop. 'Shop' path starts from it and 'Back' ends in it.
shop = Location(31958, 31985, 7) # Spot near shop, player enters shop from it
shop_name = 'Isa\'s Potions' # Change to your shop name which you will be using

# Format: itemId: buy count ...
# Set count to 999 or so to buy as many as possible.
buy_items = { 5256: 2, 5567: 1, 5569: 3 } # 2 Eggs, 1 Health potion, 3 Small mana potions

# Should go to shop check settings.
# True = bot will check for items in backpack + inventory, False = bot will check for items in backpack only.
countItemsInventory = True

# If you're using item storage feature in BOT, set this to True.
# Make sure you're using at least one item from 'buy_items' list in bot storage settings.
usingItemStorage = True

# Time for tick event.
tickTime = 15

# Paths
# Make hunting path in set 0.
# Make to shop path in set 1.
# Make back to hunt place path in set 2.
hunt = 0
to_shop = 1
back = 2

# Don't modify these.
ignore_menu = 0
last_time_shop = 0
bought = { }
buy_option_id = 1
canEnterShop = True
shopTaskRunning = False

def onTick():
	global last_time_shop, canEnterShop
	
	if last_time_shop > 0 and shopTaskRunning == False:
		cur_time = script.GetCurrentTime()
		if (cur_time - last_time_shop) > tickTime:
			last_time_shop = 0
			canEnterShop = True
			script.PauseMovement(False)
			if script.IsInShop():
				script.StatusMessage('Was stuck outside...')
				runTask()
			elif script.GetWay() == getToShopPath():
				script.StatusMessage('Was stuck...')
				script.LeaveShop()

def onScriptActivation():
	global last_time_shop, canEnterShop, shopTaskRunning
	last_time_shop = 0
	canEnterShop = True
	shopTaskRunning = False
	script.PauseMovement(False)
	bought.clear()
	script.EnableTickEvent(5000)

def getToShopPath():
	return to_shop
	
def getToHuntPath():
	return back

def onReceiveEnteredMenu(shopPacket, menuId, title):
	global ignore_menu, last_time_shop
	
	if title == shop_name:
		ignore_menu = 0
		last_time_shop = script.GetCurrentTime()
		script.StatusMessage('Shop: ' + title)
		if shopPacket == 1:
			script.PauseMovement(True)
			script.ChooseShopOption(menuId, buy_option_id) # Buy
	elif title == 'Buy':
		ignore_menu = 0
		last_time_shop = script.GetCurrentTime()
		script.StatusMessage('Buying items...')
	else:
		ignore_menu = 1

def boughtEnough(itemId):
	return itemId in bought and bought[itemId] >= buy_items[itemId]
	
def isDoneBuying():
	for itemId in buy_items.keys():
		if (itemId not in bought) or (bought[itemId] < buy_items[itemId]):
			return False
	return True

def onReceiveAddItemToBackpack(slot, itemId):
	if itemId not in buy_items:
		return

	if itemId in bought:
		bought[itemId] += 1
	else:
		bought[itemId] = 1

def shouldGoToShop():
	count = 0
	for itemId in buy_items.keys():
		if countItemsInventory:
			count += script.GetItemsCountWithInventory(itemId)
		else:
			count += script.GetItemsCount(itemId, False)
	return count == 0

def runTask():
	global shopTaskRunning, last_time_shop

	shopTaskRunning = True
	last_time_shop = script.GetCurrentTime()
	script.RunEvent('recheckShop', 5000)

def recheckShop():
	global canEnterShop, shopTaskRunning, last_time_shop

	last_time_shop = script.GetCurrentTime()

	script.StatusMessage('Shop rechecking task is ticking...')
	if usingItemStorage and script.IsStorageRunning():
		canEnterShop = False
		runTask()
		return

	canEnterShop = True
	xyz = Location(script.GetX(), script.GetY(), script.GetZ())

	script.PauseMovement(False)
	if xyz == shop:
		if script.GetWay() == getToShopPath():
			if script.EnterShop():
				script.StatusMessage('Entering shop.')
			else:
				script.Alarm('Can\'t find the shop.')
	shopTaskRunning = False

def onLeaveShop():
	global canEnterShop, last_time_shop
	
	last_time_shop = script.GetCurrentTime()

	if usingItemStorage and script.GetFreeInventorySlot() != 255:
		canEnterShop = False
		runTask()
		return

	if script.GetWay() != getToHuntPath():
		script.SetWay(getToHuntPath(), 2)

	bought.clear()
	canEnterShop = True
	script.PauseMovement(False)

def onReceiveMenuRows(rows):
	global last_time_shop

	if ignore_menu == 1:
		return

	if isDoneBuying():
		script.StatusMessage('Bought everything. Leaving shop.')
		onLeaveShop()
		script.LeaveShop()
		return

	if script.GetFreeBackpackSlot() == 255:
		script.StatusMessage('No room in your backpack. Leaving shop.')
		onLeaveShop()
		script.LeaveShop()
		return

	found = 0

	for row in rows:
		list = row.split()
		menuId = int(list[0])
		rowId = int(list[1])
		itemId = int(list[-1])
			
		if itemId not in buy_items:
			continue

		last_time_shop = script.GetCurrentTime()
		found = 1

		if boughtEnough(itemId): # Check if bought enough items
			script.StatusMessage('Bought enough: ' + str(itemId))
			continue

		script.ChooseMenuOption(menuId, 1, rowId) # Buy item
		break # break to avoid flood

	if found == 0:
		script.StatusMessage('Done.')
		onLeaveShop()
		script.LeaveShop()

def onReceiveMenuText(menuId, title, text):
	if 'No entry in the list' in text:
		script.StatusMessage('Nothing to buy!')
		onLeaveShop()
		script.LeaveShop()

def onChangeLocation(x, y, z):
	xyz = Location(x, y, z)

	if xyz == spot:
		bought.clear()
		if shouldGoToShop():
			if script.GetWay() != getToShopPath():
				script.StatusMessage('Going to shop to buy items...')
				script.SetWay(getToShopPath(), 2)
		else:
			if script.GetWay() == getToHuntPath():
				script.StatusMessage('Hunt started!')
				script.SetWay(hunt, 2)
	elif xyz == shop and canEnterShop:
		if script.GetWay() == getToShopPath():
			if script.EnterShop():
				script.StatusMessage('Entering shop.')
			else:
				script.Alarm('Can\'t find the shop.')
