"""Scoped fallback for the current Chinese weekly-missions tab font."""
def install():
    from module.automation.automation import Automation
    from module.logger import log

    original_click = Automation.click_element

    def click_element(self, target, *args, **kwargs):
        result = original_click(self, target, *args, **kwargs)
        if result or target != 'pass/weekly_assets.png':
            return result
        if args or kwargs.get('find_type', 'image') != 'image' or not kwargs.get('click', True):
            return result
        if self.take_screenshot() is None:
            return False
        position = self.find_text_element('周常任务')
        if position:
            x, y = position
            width, height = self.screenshot.size
            # Accept only the side tab, not text from a mission description.
            if 0 < x < width * .27 and height * .35 < y < height * .75:
                log.debug('周常任务标签图片不匹配，使用已定位的 OCR 文字点击')
                self.mouse_click(x, y)
                return True
        return False

    Automation.click_element = click_element
