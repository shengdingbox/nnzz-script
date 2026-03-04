package main

import (
	"fmt"
	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/widget"
)

func main() {
	fmt.Println("开始执行测试程序...")
	a := app.New()
	fmt.Println("创建应用成功")
	w := a.NewWindow("测试窗口")
	fmt.Println("创建窗口成功")
	w.SetContent(widget.NewLabel("Hello, Fyne!"))
	fmt.Println("设置内容成功")
	w.Resize(fyne.NewSize(400, 300))
	fmt.Println("设置窗口大小成功")
	fmt.Println("显示窗口...")
	w.ShowAndRun()
	fmt.Println("程序结束")
}
