from MethodNode import MethodNode

class ClassNode:
    def __init__(self, classInfo, classMapping=None):
        self._classInfo = classInfo
        self._methods = []
        self._classMapping = classMapping
        for n,i in classInfo['methods'].items():
            self._methods.append(MethodNode(n, i, self._classInfo['name'], classMapping))

    def _generateMisc(self):
        return u"#pragma once\n\n"

    def _generateHeaderIncludes(self):
        includeSet = set()
        res = u""
        for m in self._methods:
            includeSet.update(m.headerIncludes())

        for i in includeSet:
            res += u"#include " + i + u"\n"

        res += u"#include <jni.h>\n"
        return res

    def _generateDefaultConstructorDefinition(self):
        return u"    " + self._classInfo['name'] + u"(bool derrivedInstance=false);"

    def headerString(self):
        res = self._generateMisc()
        res += self._generateHeaderIncludes()

        res += u"\nclass " + self._classInfo['name']
        if 'super' in self._classInfo:
            res += u" : public " + self._classInfo['super']
        res += u" {\n"
        res += u"public:\n"
        res += self._generateDefaultConstructorDefinition() + u"\n"

        for m in self._methods:
            if m.isPublic():
                res += u"    " + m.signature() + u"\n"

        res += u"\nprotected:\n"
        res += u"    jobject jthis_;\n"

        res += u"    static jclass jclass_;\n"
        res += u"    static jmethodID jctor_;\n"
        for m in self._methods:
            if m.isPublic():
                res += u"    static jmethodID " + m.getJNIName() + u";\n"

        res += u"\nprotected:\n"
        res += "    static void jInit();\n"
        res += u"};"

        return res

    def _includeCPP(self):
        res = u"#include \"" + self._classInfo['name'] + ".h\"\n"
        res += u"#include \"JNISingleton.h\""
        return res

    def _generateDefaultConstructorBody(self):
        res = self._classInfo['name'] + u"::" + self._classInfo['name'] + u"(bool derrivedInstance)"
        if "super" in self._classInfo:
            res += u" : " + self._classInfo["super"] + "(true) "
        res += "{\n"
        res += u"    if (jclass_ == nullptr) {\n"
        res += u"        jInit();\n"
        res += u"    }\n"
        res += u"    if (derrivedInstance) return;\n"
        res += u"    jthis_ = JNISingleton::env()->NewObject(jclass_, jctor_);\n"
        res += self._jCheckForNull("jthis_")

        res += u"}"
        return res

    def _generateStaticInits(self):
        res = u"jclass " + self._classInfo['name'] + u"::jclass_ = nullptr;\n"
        res += u"jmethodID " + self._classInfo['name'] + u"::jctor_ = nullptr;\n"
        for m in self._methods:
            if m.isPublic():
                res += u"jmethodID " + self._classInfo['name'] + u"::" + m.getJNIName() + u" = nullptr;\n"
        return res + u"\n"

    def _jCheckForNull(self, varName, intend=4):
        intendStr = u" " * intend
        res = intendStr + u"if (" + varName + u" == nullptr) {\n"
        res += intendStr + intendStr + u"throw std::runtime_error(\"" + varName + " should not be nullptr\");\n"
        res += intendStr + u"}\n"
        return res

    def _generateJInit(self):
        res = u"void " + self._classInfo["name"] + u"::jInit() {\n"
        res += u"    jclass_ = JNISingleton::env()->FindClass(\"" + self._classInfo["name"] + u"\");\n"
        res += self._jCheckForNull("jclass_")
        res += u"    jctor_ = JNISingleton::env()->GetMethodID(jclass_, \"<init>\", \"()V\");\n"
        res += self._jCheckForNull("jctor_")
        for m in self._methods:
            res+= m.getJNIMethodFindLine()
            res += self._jCheckForNull(m.getJNIName())
        res += u"}\n"
        return res

    def _generateNamespacesUsage(self):
        return u"using namespace JNIWrappers;\n\n"

    def cppString(self):
        res = self._includeCPP() + u"\n\n"
        res += self._generateNamespacesUsage()
        res += self._generateStaticInits()
        res += self._generateJInit()
        res += self._generateDefaultConstructorBody() + u"\n\n"

        for m in self._methods:
            if m.isPublic():
                res += m.bodyAndSignature() + u"\n\n"

        return res