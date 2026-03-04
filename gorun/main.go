package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/md5"
	"crypto/rand"
	"crypto/sha1"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"os"
	"os/exec"
	"strings"
	"syscall"
	"time"
	"unsafe"

	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/dialog"
	"fyne.io/fyne/v2/widget"
	"golang.org/x/sys/windows/registry"
)

func main() {
	fmt.Println(">>> MAIN START")
}

const (
	TAFANG_EXE_NAME              = "tafangmonitor.exe"
	TASK_EXE_NAME                = "tafangrunning.exe"
	SECRET_KEY                   = "sd_secure_2026_custom_888"
	SALT                         = "shengding_t_2026_secure_888_xyz_123"
	ITERATIONS                   = 100000
	DATE_FORMAT                  = "20060102"
	DISPLAY_DATE_FORMAT          = "2006-01-02"
	REG_PATH                     = "Software\\ShengDingAssistant_Pro"
	REG_KEY                      = "SD_LICENSE_DATA"
	ACTIVATE_CODE_EXPIRE_MINUTES = 30
	CHECK_INTERVAL               = 60 * time.Second
)

var SUPPORT_DAYS = map[string]float64{
	"1小时": 1.0 / 24,
	"3小时": 0.125,
	"1天":  1,
	"3天":  3,
	"7天":  7,
	"30天": 30,
}

// 全局变量
var (
	hwid         string
	todayRaw     string
	licenseValid bool
	licenseData  map[string]interface{}
	watchdogDone chan bool
	logText      *widget.Entry
	mainWindow   fyne.Window
	mainApp      fyne.App
)

// Logger 日志结构体
type Logger struct{}

func (l *Logger) log(level, message string) {
	timestamp := time.Now().Format("2006-01-02 15:04:05")
	logMessage := fmt.Sprintf("[%s] %s: %s\n", timestamp, level, message)
	if logText != nil {
		logText.SetText(logText.Text + logMessage)
	}
}

func (l *Logger) Info(message string)    { l.log("INFO", message) }
func (l *Logger) Error(message string)   { l.log("ERROR", message) }
func (l *Logger) Warning(message string) { l.log("WARNING", message) }

var logger = &Logger{}

// 初始化函数
func init() {
	fmt.Println("INIT START")
	hwid = getHWID()
	todayRaw = time.Now().Format(DISPLAY_DATE_FORMAT)
	licenseValid = isLicenseValid()
	if licenseValid {
		licenseData = loadLicense()
	}
	watchdogDone = make(chan bool, 1)
}

// 生成机器码
func getHWID() string {
	info := fmt.Sprintf("%s%s%s%s%s%s",
		os.Getenv("OS"),
		os.Getenv("COMPUTERNAME"),
		os.Getenv("PROCESSOR_IDENTIFIER"),
		os.Getenv("USERNAME"),
		os.Getenv("SYSTEMROOT"),
		os.Getenv("OS"),
	)
	if info == "" || strings.TrimSpace(info) == "" {
		// 生成随机机器码
		randomBytes := make([]byte, 32)
		io.ReadFull(rand.Reader, randomBytes)
		info = string(randomBytes)
	}

	// 使用MD5哈希，然后取中间16位，再进行一次SHA1哈希
	md5Hash := md5.Sum([]byte(info))
	midPart := hex.EncodeToString(md5Hash[:])[8:24]
	sha1Hash := sha1.Sum([]byte(midPart))
	return strings.ToUpper(hex.EncodeToString(sha1Hash[:])[:16])
}

// 生成今天的哈希
func getTodayHash() string {
	todayRaw := time.Now().Format(DATE_FORMAT)
	hash := sha256.Sum256([]byte(todayRaw))
	return strings.ToUpper(hex.EncodeToString(hash[:])[:16])
}

// 生成时间令牌
func getTimeToken() string {
	now := time.Now()
	return now.Format("2006010215") + fmt.Sprintf("%d", now.Minute()/ACTIVATE_CODE_EXPIRE_MINUTES)
}

// 生成激活码
func makeActivateCode(hwid string, days float64) string {
	todayHash := getTodayHash()
	timeToken := getTimeToken()
	rawStr := fmt.Sprintf("%s|%s|%v|%s|%s", todayHash, hwid, days, timeToken, SECRET_KEY)
	hash := sha256.Sum256([]byte(rawStr))
	return strings.ToUpper(hex.EncodeToString(hash[:])[:16])
}

// 验证激活码
func verifyActivateCode(hwid, inputCode string) float64 {
	todayHash := getTodayHash()
	now := time.Now()
	validTokens := make(map[string]bool)

	// 生成有效令牌
	for minuteDelta := 0; minuteDelta <= ACTIVATE_CODE_EXPIRE_MINUTES; minuteDelta++ {
		checkTime := now.Add(-time.Duration(minuteDelta) * time.Minute)
		token := checkTime.Format("2006010215") + fmt.Sprintf("%d", checkTime.Minute()/ACTIVATE_CODE_EXPIRE_MINUTES)
		validTokens[token] = true
	}

	// 验证激活码
	for _, daysValue := range SUPPORT_DAYS {
		for token := range validTokens {
			rawStr := fmt.Sprintf("%s|%s|%v|%s|%s", todayHash, hwid, daysValue, token, SECRET_KEY)
			hash := sha256.Sum256([]byte(rawStr))
			validCode := strings.ToUpper(hex.EncodeToString(hash[:])[:16])
			if inputCode == validCode {
				return daysValue
			}
		}
	}

	return 0
}

// deriveKey 从密钥和盐值派生AES密钥
func deriveKey() []byte {
	key := []byte(SECRET_KEY)
	salt := []byte(SALT)

	// 使用PBKDF2派生密钥 (简化版本，实际应使用golang.org/x/crypto/pbkdf2)
	data := append(key, salt...)
	for i := 0; i < ITERATIONS/1000; i++ {
		hash := sha256.Sum256(data)
		data = hash[:]
	}
	return data[:32] // AES-256需要32字节密钥
}

// encryptData AES加密数据
func encryptData(data map[string]interface{}) string {
	key := deriveKey()

	// 序列化数据为JSON
	var jsonParts []string
	for k, v := range data {
		jsonParts = append(jsonParts, fmt.Sprintf(`"%s":%q`, k, v))
	}
	jsonData := "{" + strings.Join(jsonParts, ",") + "}"

	block, err := aes.NewCipher(key)
	if err != nil {
		return ""
	}

	plaintext := []byte(jsonData)
	ciphertext := make([]byte, aes.BlockSize+len(plaintext))
	iv := ciphertext[:aes.BlockSize]

	if _, err := io.ReadFull(rand.Reader, iv); err != nil {
		return ""
	}

	stream := cipher.NewCFBEncrypter(block, iv)
	stream.XORKeyStream(ciphertext[aes.BlockSize:], plaintext)

	return hex.EncodeToString(ciphertext)
}

// decryptData AES解密数据
func decryptData(encryptedHex string) map[string]interface{} {
	key := deriveKey()

	ciphertext, err := hex.DecodeString(encryptedHex)
	if err != nil {
		return nil
	}

	block, err := aes.NewCipher(key)
	if err != nil {
		return nil
	}

	if len(ciphertext) < aes.BlockSize {
		return nil
	}

	iv := ciphertext[:aes.BlockSize]
	ciphertext = ciphertext[aes.BlockSize:]

	stream := cipher.NewCFBDecrypter(block, iv)
	stream.XORKeyStream(ciphertext, ciphertext)

	// 简单解析JSON
	result := make(map[string]interface{})
	text := string(ciphertext)

	// 手动解析简单的JSON格式
	if strings.Contains(text, `"hwid":`) {
		// 提取各个字段的值
		fields := []string{"hwid", "activate_code", "days", "expire_time", "activated_time", "activated"}
		for _, field := range fields {
			pattern := fmt.Sprintf(`"%s":"`, field)
			if idx := strings.Index(text, pattern); idx != -1 {
				start := idx + len(pattern)
				end := strings.Index(text[start:], `"`)
				if end != -1 {
					result[field] = text[start : start+end]
				}
			}
		}
	}

	return result
}

// saveLicense 保存许可证到注册表
func saveLicense(hwid, code string, days float64) bool {
	expireTime := time.Now().Add(time.Duration(days*24) * time.Hour)
	licenseData = map[string]interface{}{
		"hwid":           hwid,
		"activate_code":  code,
		"days":           fmt.Sprintf("%v", days),
		"expire_time":    expireTime.Format("2006-01-02 15:04:05"),
		"activated_time": time.Now().Format("2006-01-02 15:04:05"),
		"activated":      "true",
	}

	encryptedData := encryptData(licenseData)
	if encryptedData == "" {
		return false
	}

	// 写入注册表
	key, _, err := registry.CreateKey(registry.CURRENT_USER, REG_PATH, registry.ALL_ACCESS)
	if err != nil {
		return false
	}
	defer key.Close()

	err = key.SetStringValue(REG_KEY, encryptedData)
	return err == nil
}

// loadLicense 从注册表加载许可证
func loadLicense() map[string]interface{} {
	key, err := registry.OpenKey(registry.CURRENT_USER, REG_PATH, registry.READ)
	if err != nil {
		return nil
	}
	defer key.Close()

	encryptedData, _, err := key.GetStringValue(REG_KEY)
	if err != nil {
		return nil
	}

	licenseData := decryptData(encryptedData)
	if licenseData == nil {
		// 删除无效的注册表键
		registry.DeleteKey(registry.CURRENT_USER, REG_PATH)
		return nil
	}

	return licenseData
}

// isLicenseValid 验证许可证是否有效
func isLicenseValid() bool {
	licenseData := loadLicense()
	if licenseData == nil || licenseData["activated"] != "true" {
		return false
	}

	// 验证机器码
	if licenseData["hwid"] != hwid {
		registry.DeleteKey(registry.CURRENT_USER, REG_PATH)
		return false
	}

	// 验证过期时间
	expireTimeStr, ok := licenseData["expire_time"].(string)
	if !ok {
		registry.DeleteKey(registry.CURRENT_USER, REG_PATH)
		return false
	}

	expireTime, err := time.Parse("2006-01-02 15:04:05", expireTimeStr)
	if err != nil {
		registry.DeleteKey(registry.CURRENT_USER, REG_PATH)
		return false
	}

	if time.Now().After(expireTime) {
		registry.DeleteKey(registry.CURRENT_USER, REG_PATH)
		return false
	}

	return true
}

// 终止进程
func killProcessByName(processName string) bool {
	killed := false
	processName = strings.ToLower(processName)

	// 创建系统快照
	snapshot, err := syscall.CreateToolhelp32Snapshot(syscall.TH32CS_SNAPPROCESS, 0)
	if err != nil {
		return false
	}
	defer syscall.CloseHandle(snapshot)

	var processEntry syscall.ProcessEntry32
	processEntry.Size = uint32(unsafe.Sizeof(processEntry))

	// 遍历进程列表
	for err := syscall.Process32First(snapshot, &processEntry); err == nil; err = syscall.Process32Next(snapshot, &processEntry) {
		// 将UTF16转换为字符串
		exeName := strings.ToLower(syscall.UTF16ToString(processEntry.ExeFile[:]))
		if exeName == processName {
			// 打开进程
			handle, err := syscall.OpenProcess(syscall.PROCESS_TERMINATE, false, processEntry.ProcessID)
			if err == nil {
				// 终止进程
				syscall.TerminateProcess(handle, 0)
				syscall.CloseHandle(handle)
				killed = true
			}
		}
	}

	return killed
}

// 静默终止所有脚本
func stopAllScriptsSilent() {
	killProcessByName(TAFANG_EXE_NAME)
	killProcessByName(TASK_EXE_NAME)
}

// 后台监控线程
func licenseWatchdog() {
	ticker := time.NewTicker(CHECK_INTERVAL)
	defer ticker.Stop()

	for {
		select {
		case <-watchdogDone:
			return
		case <-ticker.C:
			if !isLicenseValid() {
				stopAllScriptsSilent()
				logger.Warning("授权已到期，脚本已终止！")
				return
			}
		}
	}
}

// 复制到剪贴板
func copyToClipboard(text string) error {
	cmd := exec.Command("cmd", "/c", "echo", text, "|", "clip")
	return cmd.Run()
}

// 显示消息框
func showMessage(title, message string) {
	if mainWindow != nil {
		dialog.ShowInformation(title, message, mainWindow)
	}
}

// 启动脚本
func startScript(valid bool) {
	if !valid {
		logger.Warning("未激活/授权已到期，无法启动脚本！")
		showMessage("提示", "未激活/授权已到期，无法启动脚本！")
		return
	}

	// 获取可执行文件所在目录
	exePath, err := os.Executable()
	if err != nil {
		logger.Error("获取程序路径失败：" + err.Error())
		showMessage("错误", "获取程序路径失败！")
		return
	}

	tafangExePath := exePath[:strings.LastIndex(exePath, string(os.PathSeparator))+1] + TAFANG_EXE_NAME

	// 检查文件是否存在
	if _, err := os.Stat(tafangExePath); os.IsNotExist(err) {
		logger.Error("核心文件缺失：" + tafangExePath)
		showMessage("错误", "核心文件缺失，请重新获取软件！")
		return
	}

	// 启动脚本
	cmd := exec.Command(tafangExePath)
	cmd.SysProcAttr = &syscall.SysProcAttr{
		HideWindow: true,
	}
	err = cmd.Start()
	if err != nil {
		logger.Error("启动失败：" + err.Error())
		showMessage("启动失败", "错误信息：\n"+err.Error())
		return
	}

	logger.Info("塔防脚本启动成功！")
	showMessage("成功", "塔防脚本启动成功！")
}

// 停止脚本
func stopScript(valid bool) {
	if !valid {
		logger.Warning("未激活/授权已到期，无需终止脚本！")
		showMessage("提示", "未激活/授权已到期，无需终止脚本！")
		return
	}

	monitorKilled := killProcessByName(TAFANG_EXE_NAME)
	taskKilled := killProcessByName(TASK_EXE_NAME)

	if monitorKilled || taskKilled {
		logger.Info("已终止所有运行的脚本！")
		showMessage("成功", "已终止所有运行的脚本！")
	} else {
		logger.Info("未检测到运行中的脚本！")
		showMessage("提示", "未检测到运行中的脚本！")
	}
}

// 主函数
func main() {
	// 创建应用
	fmt.Println("INIT START")
	mainApp = app.New()
	mainWindow = mainApp.NewWindow("塔防自动化助手 - 专业版")
	mainWindow.Resize(fyne.NewSize(700, 650))

	// 标题区域
	titleLabel := widget.NewLabelWithStyle("逆战未来塔防盛鼎脚本", fyne.TextAlignLeading, fyne.TextStyle{Bold: true})
	lightningLabel := widget.NewLabel("⚡")
	titleBox := container.NewHBox(titleLabel, lightningLabel)

	// 状态区域
	statusText := "未激活 | 请输入激活码"
	if licenseValid && licenseData != nil {
		if expireTime, ok := licenseData["expire_time"].(string); ok {
			statusText = "已激活 | 到期：" + expireTime
		}
	}
	statusLabel := widget.NewLabelWithStyle(statusText, fyne.TextAlignLeading, fyne.TextStyle{Bold: true})

	// 公告区域
	announcementTexts := []string{
		"• 一机一码，激活后绑定本机",
		"欢迎使用逆战未来塔防盛鼎脚本",
		"遇到问题请前往群文件更新到最新版",
		"游戏每隔一段时间就会来一次大批量检测行为和检测历史战绩记录，请合理安排挂机时间，尽量不要一直挂机，导致禁赛。",
	}
	announcementBox := container.NewVBox()
	for _, text := range announcementTexts {
		announcementBox.Add(widget.NewLabel(text))
	}

	// 激活中心区域
	// 机器码
	hwidLabel := widget.NewLabel("机器码：")
	hwidValue := widget.NewLabel(hwid)
	copyButton := widget.NewButton("复制", func() {
		err := copyToClipboard(hwid)
		if err != nil {
			showMessage("提示", "请安装剪贴板工具以使用复制功能")
		} else {
			showMessage("提示", "✅ 复制成功")
		}
	})
	hwidBox := container.NewHBox(hwidLabel, hwidValue, copyButton)

	// 激活码
	activateCodeLabel := widget.NewLabel("激活码：")
	activateCodeEntry := widget.NewEntry()
	activateCodeEntry.SetPlaceHolder("请输入16位激活码")
	activateButton := widget.NewButton("立即激活", func() {
		inputCode := strings.ToUpper(strings.TrimSpace(activateCodeEntry.Text))
		if len(inputCode) != 16 {
			logger.Warning("激活码必须是16位字符！")
			showMessage("提示", "激活码必须是16位字符！")
			return
		}

		validDays := verifyActivateCode(hwid, inputCode)
		if validDays > 0 {
			saveLicense(hwid, inputCode, validDays)
			daysName := ""
			for name, value := range SUPPORT_DAYS {
				if value == validDays {
					daysName = name
					break
				}
			}
			logger.Info("激活成功：已激活" + daysName + "权限！")
			showMessage("激活成功", "已激活"+daysName+"权限！程序将重启生效")
			// 重启程序
			mainWindow.Close()
			exec.Command(os.Args[0]).Start()
		} else {
			logger.Error("激活失败：激活码无效、已过期（30分钟内有效）或不匹配本机！")
			showMessage("激活失败", "激活码无效、已过期（30分钟内有效）或不匹配本机！")
		}
	})
	activateCodeBox := container.NewHBox(activateCodeLabel, activateCodeEntry, activateButton)
	activationBox := container.NewVBox(hwidBox, activateCodeBox)

	// 功能按钮区域
	startButton := widget.NewButton("启动塔防脚本 (F2)", func() {
		startScript(licenseValid)
	})
	if !licenseValid {
		startButton.Disable()
	}

	stopButton := widget.NewButton("终止所有脚本 (F10)", func() {
		stopScript(licenseValid)
	})
	if !licenseValid {
		stopButton.Disable()
	}

	buttonBox := container.NewHBox(startButton, stopButton)

	// 日志输出区域
	logText = widget.NewMultiLineEntry()
	logText.SetPlaceHolder("运行日志...")
	logText.Disable()

	// 主布局
	content := container.NewBorder(
		container.NewVBox(
			titleBox,
			statusLabel,
			widget.NewSeparator(),
			announcementBox,
			widget.NewSeparator(),
			activationBox,
			widget.NewSeparator(),
			buttonBox,
		),
		logText,
		nil,
		nil,
	)

	mainWindow.SetContent(content)

	// 启动授权监控线程
	if licenseValid {
		go licenseWatchdog()
	}

	// 窗口关闭处理
	mainWindow.SetOnClosed(func() {
		stopAllScriptsSilent()
		select {
		case watchdogDone <- true:
		default:
		}
	})

	// 运行主循环
	mainWindow.ShowAndRun()
}
